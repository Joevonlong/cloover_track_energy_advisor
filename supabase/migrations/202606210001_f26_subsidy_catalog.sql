-- F26: DB-driven subsidy catalog (mirror of price_catalog).
-- Subsidies feed money math (capex_after_subsidy → installment → North Star),
-- so the ENGINE only ever reads this gated table — never a crawler's raw output.
-- This migration is intentionally re-runnable and offline-safe (AC1, AC2, R9).
--
-- Pre-demo procedure (R-C): Lukas verifies every source_url against the official
-- page and signs off before the demo. valid_until gates expired rows out with
-- zero code change.

create table if not exists public.subsidy_catalog (
    programme    text not null,                 -- e.g. 'kfw_458_base', 'vat_pv_battery'
    component    text not null,                 -- 'heat_pump_a'|'heat_pump_b'|'pv'|'battery'|'ev_charger'
    rate         numeric not null check (rate >= 0 and rate <= 1),  -- fraction_of_capex
    cap_eur      numeric check (cap_eur is null or cap_eur >= 0),   -- absolute grant cap; null = uncapped
    unit         text not null default 'fraction_of_capex',
    source_url   text not null check (length(trim(source_url)) > 0),
    valid_from   date not null,
    valid_until  date,                           -- null = open-ended
    notes        text,
    primary key (programme, component, valid_from)
);

create index if not exists subsidy_catalog_lookup_idx
    on public.subsidy_catalog (component, valid_from desc);

-- Hybrid sourcing: the weekly crawler writes PROPOSED changes here, never to
-- subsidy_catalog directly. A human (or the engine's gating) decides whether a
-- proposal is promoted — a bad scrape can never corrupt the live rate.
create table if not exists public.subsidy_catalog_staging (
    id            uuid primary key default gen_random_uuid(),
    programme     text not null,
    component     text not null,
    rate          numeric,
    cap_eur       numeric,
    source_url    text not null,
    crawled_at    timestamptz not null default now(),
    raw_excerpt   text,                          -- the snippet the LLM parsed
    diff_note     text,                          -- how it differs from the live row
    status        text not null default 'proposed' -- 'proposed'|'promoted'|'rejected'
        check (status in ('proposed', 'promoted', 'rejected'))
);

create index if not exists subsidy_staging_status_idx
    on public.subsidy_catalog_staging (status, crawled_at desc);

-- ── Seed: the six MVP federal rows (§12.1). Idempotent. ───────────────────────
-- Every rate cited to its official/legal source. No number is invented.
insert into public.subsidy_catalog
    (programme, component, rate, cap_eur, unit, source_url, valid_from, valid_until, notes)
values
    -- KfW 458 base grant — applies to BOTH heat-pump cases (new fossil→HP and old-HP→HP).
    ('kfw_458_base', 'heat_pump_a', 0.30, 21000, 'fraction_of_capex',
     'https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/F%C3%B6rderprodukte/Heizungsf%C3%B6rderung-f%C3%BCr-Privatpersonen-Wohngeb%C3%A4ude-(458)/',
     date '2026-06-20', null,
     'Grundförderung 30%. Eligible cost capped at €30,000 (first dwelling) → max grant €21,000; combined KfW rate capped at 70%.'),
    ('kfw_458_base', 'heat_pump_b', 0.30, 21000, 'fraction_of_capex',
     'https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/F%C3%B6rderprodukte/Heizungsf%C3%B6rderung-f%C3%BCr-Privatpersonen-Wohngeb%C3%A4ude-(458)/',
     date '2026-06-20', null,
     'Grundförderung 30% also applies to replacing an old/inefficient heat pump (Case B). No speed bonus in Case B.'),
    -- Klima-Geschwindigkeitsbonus — Case A ONLY (replacing a functioning fossil system).
    ('kfw_458_speed_bonus', 'heat_pump_a', 0.20, 21000, 'fraction_of_capex',
     'https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/F%C3%B6rderprodukte/Heizungsf%C3%B6rderung-f%C3%BCr-Privatpersonen-Wohngeb%C3%A4ude-(458)/',
     date '2026-06-20', null,
     'Klima-Geschwindigkeitsbonus 20% for replacing a fossil heating system. NOT available for old-HP→HP (Case B) — see R4/§5.3.'),
    -- 0% VAT on PV + battery (§12(3) UStG) — modelled as a 0.00 capex fraction (price already net).
    ('vat_pv_battery', 'pv', 0.00, null, 'fraction_of_capex',
     'https://www.gesetze-im-internet.de/ustg_1980/__12.html',
     date '2026-06-20', null,
     '0% VAT under §12(3) UStG. Prices in price_catalog are already net of VAT; this row documents the relief and its source.'),
    ('vat_pv_battery', 'battery', 0.00, null, 'fraction_of_capex',
     'https://www.gesetze-im-internet.de/ustg_1980/__12.html',
     date '2026-06-20', null,
     '0% VAT under §12(3) UStG, including batteries added to an existing PV system.'),
    -- BAFA EV Umweltbonus — ENDED 17 Dec 2023. Kept as a gated row so the demo can show "ended", not "missing".
    ('bafa_ev_umweltbonus', 'ev_charger', 0.00, 0, 'fraction_of_capex',
     'https://www.bafa.de/DE/Energie/Energieeffizienz/Elektromobilitaet/elektromobilitaet_node.html',
     date '2020-01-01', date '2023-12-17',
     'Umweltbonus ended 17 Dec 2023. rate=0, cap=0; valid_until gates it out for any request after that date.')
on conflict (programme, component, valid_from) do update set
    rate = excluded.rate,
    cap_eur = excluded.cap_eur,
    unit = excluded.unit,
    source_url = excluded.source_url,
    valid_until = excluded.valid_until,
    notes = excluded.notes;
