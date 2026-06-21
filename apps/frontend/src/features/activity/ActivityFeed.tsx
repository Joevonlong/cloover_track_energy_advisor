// Phase 4B — live activity feed (light Pactum "Agent feed" style). Renders the
// recommendation + roof progress as a stream of status rows.
export type ActivityStatus = "ok" | "warn" | "info" | "loading";

export interface ActivityEvent {
  id: string;
  /** Pre-formatted clock label, e.g. "14:32". */
  timestamp: string;
  /** Bold lead-in (the "agent" / layer name). */
  source: string;
  /** Body line. */
  label: string;
  status: ActivityStatus;
}

// Tailwind colour pairs per status: [avatar bg, avatar text, glyph].
const AVATAR: Record<ActivityStatus, { bg: string; fg: string; glyph: string }> = {
  ok: { bg: "bg-[#ecfdf5]", fg: "text-[#059669]", glyph: "✓" },
  warn: { bg: "bg-[#fef2f2]", fg: "text-[#dc2626]", glyph: "!" },
  info: { bg: "bg-[#eff6ff]", fg: "text-[#2563eb]", glyph: "i" },
  loading: { bg: "bg-[var(--surface)]", fg: "text-[var(--text-3)]", glyph: "" },
};

export interface ActivityFeedProps {
  events: ActivityEvent[];
}

export default function ActivityFeed({ events }: ActivityFeedProps) {
  return (
    <aside className="flex h-full flex-col border-l border-[var(--border)] bg-white">
      <header className="flex items-start justify-between px-5 py-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--text-3)]">
            Live activity
          </p>
          <h2 className="mt-0.5 text-[15px] font-bold tracking-[-0.01em] text-[var(--text-1)]">
            Agent feed
          </h2>
        </div>
        <span className="flex items-center gap-1.5 text-[12px] font-medium text-[var(--text-2)]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#10b981]" />
          {events.length} events
        </span>
      </header>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {events.length === 0 ? (
          <p className="px-3 py-4 text-[12px] text-[var(--text-3)]">Waiting for checks…</p>
        ) : (
          <ul className="space-y-0.5">
            {events.map((e) => {
              const a = AVATAR[e.status];
              return (
                <li
                  key={e.id}
                  className="flex items-start gap-3 rounded-xl px-3 py-3 transition-colors hover:bg-[var(--surface)]"
                >
                  {e.status === "loading" ? (
                    <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--surface)]">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--border-strong)] border-t-[var(--text-2)]" />
                    </span>
                  ) : (
                    <span
                      className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[14px] font-bold ${a.bg} ${a.fg}`}
                    >
                      {a.glyph}
                    </span>
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline justify-between gap-2">
                      <p className="truncate text-[13px] font-semibold text-[var(--text-1)]">
                        {e.source}
                      </p>
                      <span className="shrink-0 text-[11px] tabular-nums text-[var(--text-3)]">
                        {e.timestamp}
                      </span>
                    </div>
                    <p className="mt-0.5 text-[12.5px] leading-snug text-[var(--text-2)]">
                      {e.label}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
