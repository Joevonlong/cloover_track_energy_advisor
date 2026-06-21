// Results screen — dark HUD shell over the globe (F20/F21/F22/F23).
// Receives a Recommendation from the API and renders the configurator ladder,
// hero saving number, bucket tiles, LLM explanation, and proposal CTA.
import { useState } from "react";
import type { Recommendation, ScenarioResult } from "@/lib/types";

// ── helpers ────────────────────────────────────────────────────────────────

function eur(n: number, opts?: { sign?: boolean }) {
  const abs = Math.abs(n);
  const formatted = abs.toLocaleString("de-DE", { maximumFractionDigits: 0 });
  if (opts?.sign) return (n >= 0 ? "+" : "−") + " €" + formatted;
  return (n < 0 ? "−" : "") + "€" + formatted;
}

function savingColor(n: number) {
  if (n > 0) return "text-[#d9f99d]";
  if (n < -10) return "text-[#fca5a5]";
  return "text-[#b7c7c0]";
}

// ── shared dark card ────────────────────────────────────────────────────────

function HudCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl border border-white/10 bg-[rgb(9_17_20/0.82)] shadow-lg backdrop-blur-xl ${className}`}
    >
      {children}
    </div>
  );
}

function Kicker({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-bold uppercase tracking-[0.10em] text-[#91a39d]">{children}</p>
  );
}

// ── F21 Hero panel ──────────────────────────────────────────────────────────

function HeroPanel({
  rec,
  selected,
}: {
  rec: Recommendation;
  selected: ScenarioResult;
}) {
  const saving = selected.monthly_saving_eur;
  const isPositive = saving > 0;

  return (
    <HudCard className="px-6 py-5">
      <Kicker>Your monthly savings</Kicker>

      <div className="mt-3 flex items-end gap-3">
        <span
          className={`text-[52px] font-extrabold leading-none tabular-nums tracking-tight ${savingColor(saving)}`}
        >
          {eur(saving)}
        </span>
        <span className="mb-1.5 text-[15px] font-semibold text-[#b7c7c0]">/mo</span>
      </div>

      <div className="mt-1 flex items-center gap-2">
        <span className="text-[13px] text-[#b7c7c0]">
          {selected.confidence.low_eur > 0
            ? `${eur(selected.confidence.low_eur)} – ${eur(selected.confidence.high_eur)}`
            : `±${eur(selected.confidence.band_eur)}`}{" "}
          confidence range
        </span>
        <span className="rounded-full bg-white/10 px-2 py-0.5 text-[11px] text-[#b7c7c0]">
          {selected.confidence.biggest_driver}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-[#91a39d]">Today</p>
          <p className="mt-0.5 text-[17px] font-bold text-white">
            {eur(rec.current_monthly_spend_eur)}/mo
          </p>
        </div>
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-[#91a39d]">
            After upgrade
          </p>
          <p className="mt-0.5 text-[17px] font-bold text-white">
            {eur(
              rec.current_monthly_spend_eur -
                selected.saving_after_payoff_eur +
                selected.installment_eur_month,
            )}
            /mo
          </p>
        </div>
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-[#91a39d]">
            After payoff
          </p>
          <p className="mt-0.5 text-[17px] font-bold text-[#d9f99d]">
            {eur(rec.current_monthly_spend_eur - selected.saving_after_payoff_eur)}/mo
          </p>
        </div>
      </div>

      {isPositive && (
        <p className="mt-3 text-[12px] text-[#b7c7c0]">
          {selected.payback_note} · break-even month {selected.break_even_month}
        </p>
      )}
    </HudCard>
  );
}

// ── F20 Configurator ladder ─────────────────────────────────────────────────

const LAYER_ICONS = ["☀️", "🔋", "♨️", "🚗"];
const LAYER_NAMES = ["Solar PV", "Battery", "Heat pump", "EV charger"];

function ConfiguratorPanel({
  rec,
  selected,
  onSelect,
}: {
  rec: Recommendation;
  selected: ScenarioResult;
  onSelect: (s: ScenarioResult) => void;
}) {
  return (
    <HudCard className="overflow-hidden">
      <div className="border-b border-white/10 px-5 py-4">
        <Kicker>Your upgrade plan</Kicker>
        <p className="mt-0.5 text-[14px] font-semibold text-[#edf7f2]">
          Choose your combination
        </p>
      </div>
      <div className="divide-y divide-white/[0.07]">
        {rec.alternatives.map((alt, i) => {
          const prev = rec.alternatives[i - 1];
          const delta =
            i === 0
              ? alt.monthly_saving_eur
              : alt.monthly_saving_eur - (prev?.monthly_saving_eur ?? 0);
          const isSelected = alt.scenario_id === selected.scenario_id;
          return (
            <button
              key={alt.scenario_id}
              type="button"
              onClick={() => onSelect(alt)}
              className={`flex w-full items-center gap-3 px-5 py-3.5 text-left transition-colors duration-150 ${
                isSelected ? "bg-white/[0.08]" : "hover:bg-white/[0.04]"
              }`}
            >
              <span className="text-[20px] leading-none">{LAYER_ICONS[i]}</span>
              <div className="min-w-0 flex-1">
                <p className="text-[13px] font-semibold text-[#edf7f2]">{LAYER_NAMES[i]}</p>
                <p className="mt-0.5 text-[11px] text-[#91a39d]">
                  {eur(alt.capex.after_subsidy_eur)} net investment ·{" "}
                  {eur(alt.installment_eur_month)}/mo installment
                </p>
              </div>
              <div className="text-right">
                <p className={`text-[15px] font-bold tabular-nums ${savingColor(delta)}`}>
                  {eur(delta, { sign: true })}/mo
                </p>
                <p className="mt-0.5 text-[11px] text-[#91a39d]">
                  cumulative {eur(alt.monthly_saving_eur, { sign: true })}/mo
                </p>
              </div>
              {isSelected && (
                <div className="ml-1 h-5 w-5 shrink-0 rounded-full bg-[#d9f99d] text-[#18200d] flex items-center justify-center text-[11px] font-bold">
                  ✓
                </div>
              )}
            </button>
          );
        })}
      </div>
    </HudCard>
  );
}

// ── F22 Bucket tiles ────────────────────────────────────────────────────────

function BucketPanel({
  rec,
  selected,
}: {
  rec: Recommendation;
  selected: ScenarioResult;
}) {
  const buckets = [
    {
      icon: "⚡",
      label: "Electricity",
      saving: selected.breakdown.electricity_eur_month,
      before: rec.current_monthly_spend_eur * 0.30,
    },
    {
      icon: "🔥",
      label: "Heating",
      saving: selected.breakdown.heating_eur_month,
      before: rec.current_monthly_spend_eur * 0.37,
    },
    {
      icon: "🚗",
      label: "Mobility",
      saving: selected.breakdown.mobility_eur_month,
      before: rec.current_monthly_spend_eur * 0.33,
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {buckets.map((b) => (
        <HudCard key={b.label} className="px-4 py-4">
          <p className="text-[20px]">{b.icon}</p>
          <p className="mt-1.5 text-[11px] font-bold uppercase tracking-wide text-[#91a39d]">
            {b.label}
          </p>
          <p className={`mt-1 text-[20px] font-extrabold tabular-nums ${savingColor(b.saving)}`}>
            {b.saving > 0 ? "−" : ""}€{Math.abs(b.saving)}
          </p>
          <p className="mt-0.5 text-[11px] text-[#b7c7c0]">per month</p>
        </HudCard>
      ))}
    </div>
  );
}

// ── F23 Proposal / CTA panel ────────────────────────────────────────────────

function ProposalPanel({ rec }: { rec: Recommendation }) {
  const [open, setOpen] = useState(false);

  return (
    <HudCard className="px-6 py-5">
      <Kicker>AI analysis</Kicker>
      <p className="mt-2 text-[14px] leading-relaxed text-[#edf7f2]">{rec.explanation_md}</p>

      {open && (
        <div className="mt-4 border-t border-white/10 pt-4">
          <p className="text-[12px] font-bold uppercase tracking-wide text-[#91a39d]">
            Assumptions
          </p>
          <div className="mt-2 space-y-1.5">
            {rec.assumptions.map((a) => (
              <div key={a.field} className="flex items-start gap-2">
                <span className="mt-0.5 rounded bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-[#b7c7c0]">
                  {a.field}
                </span>
                <span className="text-[12px] text-[#b7c7c0]">
                  {a.value} — {a.source}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          className="inline-flex h-10 items-center justify-center rounded-xl bg-[#d9f99d] px-5 text-[13px] font-bold text-[#18200d] shadow-sm transition-[filter] duration-150 hover:brightness-95 active:scale-[0.97]"
        >
          Request offer →
        </button>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="text-[12px] text-[#b7c7c0] underline-offset-2 hover:underline"
        >
          {open ? "Hide assumptions" : "Show assumptions"}
        </button>
      </div>
    </HudCard>
  );
}

// ── Root export ─────────────────────────────────────────────────────────────

export default function ResultsScreen({
  rec,
  onBack,
}: {
  rec: Recommendation;
  onBack: () => void;
}) {
  const [selected, setSelected] = useState<ScenarioResult>(rec.best);

  return (
    <div
      className="min-h-screen overflow-y-auto"
      style={{ background: "linear-gradient(160deg, #071014 0%, #0a1c22 50%, #071014 100%)" }}
    >
      <div className="mx-auto max-w-[900px] px-4 py-8 md:px-6">
        {/* top bar */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-[#91a39d]">
              Heimwende · Energy advisor
            </p>
            <h1 className="mt-0.5 text-[22px] font-extrabold text-[#edf7f2]">
              Your savings potential
            </h1>
          </div>
          <button
            type="button"
            onClick={onBack}
            className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-[13px] text-[#b7c7c0] transition-colors hover:bg-white/10"
          >
            ← Back
          </button>
        </div>

        <div className="flex flex-col gap-4">
          <HeroPanel rec={rec} selected={selected} />
          <div className="grid gap-4 md:grid-cols-[1fr_320px]">
            <div className="flex flex-col gap-4">
              <BucketPanel rec={rec} selected={selected} />
              <ProposalPanel rec={rec} />
            </div>
            <ConfiguratorPanel rec={rec} selected={selected} onSelect={setSelected} />
          </div>
        </div>
      </div>
    </div>
  );
}
