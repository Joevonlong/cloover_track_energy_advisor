"""MaStR PLZ seed job — pre-indexes solar system counts per German postal code.

Downloads the BNetzA Marktstammdatenregister daily export, counts active solar
installations per PLZ, and upserts the result into Supabase `plz_solar_count`.

Run once weekly (e.g. GitHub Action or manual):
    PYTHONPATH=src python3.12 -m app.jobs.seed_mastr

The permit layer's check_mastr() then does a single row lookup instead of
searching with Tavily — instant, accurate, free.

Spark YC equivalent: their weekly crawler pre-indexes AHJ permit data.
We do the same with structured BNetzA open data.
"""
from __future__ import annotations

import io
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import date, timedelta

import httpx

_DOWNLOAD_PAGE = "https://www.marktstammdatenregister.de/MaStR/Datendownload"
_SUPABASE_TABLE = "plz_solar_count"
_ACTIVE_STATUS = "InBetrieb"
_BATCH_SIZE = 500


def _find_export_url() -> str:
    """Scrape the MaStR download page to find today's export ZIP URL."""
    resp = httpx.get(_DOWNLOAD_PAGE, timeout=15, follow_redirects=True)
    resp.raise_for_status()
    # Find the daily export link (not Stichtag)
    urls = re.findall(
        r'href="(https://download\.marktstammdatenregister\.de/Gesamtdatenexport_\d{8}_[^"]+\.zip)"',
        resp.text,
    )
    if not urls:
        raise RuntimeError("Could not find MaStR export URL on download page")
    # First match is the daily export (Gesamtdatenauszug vom Vortag)
    return urls[0]


def _download_to_tempfile(url: str) -> str:
    """Stream-download the ZIP to a temp file. Returns the temp file path."""
    print(f"Downloading {url} ...", flush=True)
    tmp = tempfile.mktemp(suffix=".zip")
    with httpx.stream("GET", url, timeout=600, follow_redirects=True) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(tmp, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r  {pct}% ({downloaded // 1_000_000} MB)", end="", flush=True)
    print(f"\n  Downloaded {downloaded // 1_000_000} MB", flush=True)
    return tmp


def _count_solar_by_plz(zip_path: str) -> Counter[str]:
    """Parse EinheitSolar XML inside the ZIP, count active installs per PLZ."""
    counts: Counter[str] = Counter()

    with zipfile.ZipFile(zip_path, "r") as zf:
        solar_files = [n for n in zf.namelist() if "EinheitSolar" in n and n.endswith(".xml")]
        if not solar_files:
            raise RuntimeError(f"No EinheitSolar XML found in ZIP. Files: {zf.namelist()[:10]}")

        print(f"  Found solar files: {solar_files}", flush=True)

        for filename in solar_files:
            print(f"  Parsing {filename} ...", flush=True)
            with zf.open(filename) as f:
                # iterparse to avoid loading full XML into memory
                context = ET.iterparse(f, events=("end",))
                plz = None
                status = None
                n = 0

                for event, elem in context:
                    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

                    if tag == "Postleitzahl":
                        plz = (elem.text or "").strip()
                    elif tag == "EinheitBetriebsstatus":
                        status = (elem.text or "").strip()
                    elif tag == "EinheitSolar":
                        if plz and status == _ACTIVE_STATUS:
                            counts[plz] += 1
                        plz = None
                        status = None
                        elem.clear()
                        n += 1
                        if n % 100_000 == 0:
                            print(f"    Processed {n:,} units ...", flush=True)

    return counts


def _upsert_to_supabase(
    counts: Counter[str],
    supabase_url: str,
    supabase_key: str,
) -> int:
    """Upsert PLZ counts to Supabase in batches. Returns number of rows upserted."""
    base = f"{supabase_url.rstrip('/')}/rest/v1/{_SUPABASE_TABLE}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    rows = [{"plz": plz, "count": count} for plz, count in counts.items()]
    total = 0

    for i in range(0, len(rows), _BATCH_SIZE):
        batch = rows[i : i + _BATCH_SIZE]
        resp = httpx.post(base, headers=headers, json=batch, timeout=30)
        resp.raise_for_status()
        total += len(batch)
        print(f"\r  Upserted {total:,} / {len(rows):,} PLZs", end="", flush=True)

    print(flush=True)
    return total


def seed(
    supabase_url: str | None = None,
    supabase_key: str | None = None,
    *,
    dry_run: bool = False,
) -> Counter[str]:
    """Full pipeline: find URL → download → parse → upsert. Returns PLZ counter."""
    url = _find_export_url()
    print(f"Export URL: {url}", flush=True)

    zip_path = _download_to_tempfile(url)

    try:
        print("Counting solar installations per PLZ ...", flush=True)
        counts = _count_solar_by_plz(zip_path)
        print(f"  Found {len(counts):,} PLZs with solar, {sum(counts.values()):,} total units")

        if dry_run:
            print("Dry run — skipping Supabase upsert.")
            top = counts.most_common(5)
            print(f"  Top PLZs: {top}")
            return counts

        url_ = supabase_url or os.environ.get("SUPABASE_URL", "")
        key_ = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url_ or not key_:
            raise RuntimeError(
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars (or pass as args)."
            )

        print(f"Upserting to Supabase {_SUPABASE_TABLE} ...", flush=True)
        n = _upsert_to_supabase(counts, url_, key_)
        print(f"Done. Seeded {n:,} PLZs into {_SUPABASE_TABLE}.")

        sample_plz = "74722"
        if sample_plz in counts:
            print(f"  Sample: PLZ {sample_plz} → {counts[sample_plz]} active solar systems")

        return counts

    finally:
        import os as _os
        try:
            _os.unlink(zip_path)
        except OSError:
            pass


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN (no Supabase write) ===")
    try:
        seed(dry_run=dry_run)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
