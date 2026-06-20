// Tiny fetch client — backbone (F01).
// TODO F02/F18: replace these hand-written calls with the generated OpenAPI TS client.
import type { Household, Recommendation } from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}

// TODO F17/F18: wire to the real endpoint + generated types + ?fixture support.
export async function postRecommend(body: Household): Promise<Recommendation> {
  const res = await fetch(`${BASE}/api/v1/advisor/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`recommend ${res.status}`);
  return res.json();
}
