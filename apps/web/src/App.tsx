import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";
import { IntakeForm } from "@/features/intake/IntakeForm";
import { Configurator } from "@/features/configurator/Configurator";
import { Dashboard } from "@/features/dashboard/Dashboard";
import { Proposal } from "@/features/proposal/Proposal";

// App shell — backbone (F01). No features yet; the four areas below are placeholders.
export default function App() {
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth, retry: false });
  const apiStatus = health.isSuccess ? "● ok" : health.isError ? "● down" : "○ …";

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <header className="flex items-center justify-between border-b px-6 py-4">
        <span className="font-semibold">Heimwende</span>
        <span className="text-xs text-neutral-500">API: {apiStatus}</span>
      </header>

      <main className="mx-auto max-w-3xl space-y-8 px-6 py-10">
        <section className="text-center">
          <p className="text-sm uppercase tracking-wide text-neutral-500">Your saving</p>
          <p className="text-6xl font-bold tabular-nums">
            €—<span className="ml-2 text-2xl font-normal text-neutral-500">/ month</span>
          </p>
          <p className="mt-2 text-sm text-neutral-500">Backbone (F01) — features are stubbed below.</p>
        </section>

        <IntakeForm />
        <Configurator />
        <Dashboard />
        <Proposal />
      </main>
    </div>
  );
}
