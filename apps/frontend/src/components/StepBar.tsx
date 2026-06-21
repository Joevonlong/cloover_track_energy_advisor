// Top progress bar — shows the user where they are in the flow.
// Light white bar with connecting lines, check icons for completed steps.
import { Check } from "lucide-react";
import HeimwendeMark from "@/components/HeimwendeMark";

export interface Step {
  label: string;
}

const STEPS: Step[] = [
  { label: "Address" },
  { label: "Draw roof" },
  { label: "Parameters" },
  { label: "3D model" },
  { label: "Recommendation" },
];

interface StepBarProps {
  currentStep: number; // 0-based index
}

export default function StepBar({ currentStep }: StepBarProps) {
  return (
    <div
      className="absolute inset-x-0 top-0 z-20 flex items-center border-b border-border bg-white/95 px-8"
      style={{ height: 52, backdropFilter: "blur(8px)" }}
    >
      {/* Logo mark */}
      <div className="mr-8 flex shrink-0 items-center gap-2">
        <HeimwendeMark size={22} />
        <span className="text-[13px] font-bold tracking-[-0.01em] text-text-1">Heimwende</span>
      </div>

      {/* Steps */}
      <div className="flex flex-1 items-center justify-center gap-0">
        {STEPS.map((step, i) => {
          const done = i < currentStep;
          const active = i === currentStep;

          return (
            <div key={step.label} className="flex items-center">
              {/* Connector line before each step except the first */}
              {i > 0 && (
                <div
                  className="h-px w-12 transition-colors duration-300"
                  style={{
                    background: done || active ? "#2f6fed" : "#e4e7ec",
                    opacity: done ? 1 : active ? 0.5 : 1,
                  }}
                />
              )}

              {/* Step node */}
              <div className="flex items-center gap-2">
                <div
                  className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full transition-colors duration-200"
                  style={{
                    background: done
                      ? "#2f6fed"
                      : active
                        ? "#2f6fed"
                        : "transparent",
                    border: done || active ? "none" : "1.5px solid #d0d5dd",
                  }}
                >
                  {done ? (
                    <Check size={11} strokeWidth={2.5} className="text-white" />
                  ) : active ? (
                    <div className="h-2 w-2 rounded-full bg-white" />
                  ) : null}
                </div>

                <span
                  className="text-[12px] font-semibold transition-colors duration-200"
                  style={{
                    color: done || active ? "#2f6fed" : "#9ca3af",
                  }}
                >
                  {step.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Right spacer to balance the logo */}
      <div className="ml-8 shrink-0 w-[90px]" />
    </div>
  );
}
