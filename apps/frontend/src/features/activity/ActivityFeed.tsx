// Phase 4B — live activity feed (Pactum-style right panel). Renders the
// recommendation + permit progress as a stream of status rows.
export type ActivityStatus = "ok" | "warn" | "info" | "loading";

export interface ActivityEvent {
  id: string;
  /** Pre-formatted clock label, e.g. "14:32". */
  timestamp: string;
  label: string;
  status: ActivityStatus;
}

const DOT: Record<ActivityStatus, string> = {
  ok: "bg-[#d9f99d]",
  warn: "bg-[#fca5a5]",
  info: "bg-[#7dd3fc]",
  loading: "bg-[#b7c7c0]",
};

const GLYPH: Record<ActivityStatus, string> = {
  ok: "✓",
  warn: "!",
  info: "i",
  loading: "",
};

export interface ActivityFeedProps {
  events: ActivityEvent[];
}

export default function ActivityFeed({ events }: ActivityFeedProps) {
  return (
    <aside className="flex h-full flex-col border-l border-white/10 bg-[rgb(7_16_20/0.92)] backdrop-blur-xl">
      <header className="flex items-center gap-2 border-b border-white/10 px-5 py-4">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#d9f99d] opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-[#d9f99d]" />
        </span>
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#91a39d]">
          Live activity
        </p>
      </header>

      <div className="flex-1 overflow-y-auto px-3 py-3">
        {events.length === 0 ? (
          <p className="px-2 py-4 text-[12px] text-[#6f827b]">Waiting for checks…</p>
        ) : (
          <ul className="space-y-1">
            {events.map((e) => (
              <li
                key={e.id}
                className="flex items-start gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-white/[0.04]"
              >
                {e.status === "loading" ? (
                  <span className="mt-0.5 h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 border-white/20 border-t-white/70" />
                ) : (
                  <span
                    className={`mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full text-[9px] font-bold text-[#0a1c22] ${DOT[e.status]}`}
                  >
                    {GLYPH[e.status]}
                  </span>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-[12.5px] leading-snug text-[#edf7f2]">{e.label}</p>
                  <p className="mt-0.5 text-[10px] tabular-nums text-[#6f827b]">{e.timestamp}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
