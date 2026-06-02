import { ArrowRight, Sparkles } from "lucide-react";
import { VI } from "../lib/vi";

export default function DemoWorkflowBanner() {
  const steps = VI.workflow.steps;
  return (
    <div className="rounded-2xl border border-purple-100 bg-gradient-to-r from-purple-50 via-white to-blue-50 p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-purple-900">
            <Sparkles className="h-4 w-4 text-purple-600" />
            {VI.workflow.title}
          </div>
          <p className="mt-1 max-w-2xl text-xs leading-relaxed text-slate-600">
            {VI.workflow.subtitle}
          </p>
        </div>
      </div>
      <ol className="mt-4 grid gap-2 sm:grid-cols-3">
        {steps.map((step, i) => (
          <li
            key={step.title}
            className="flex items-start gap-2 rounded-xl border border-white/80 bg-white/70 px-3 py-2.5 shadow-sm"
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-purple-600 text-[11px] font-bold text-white">
              {i + 1}
            </span>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-slate-900">{step.title}</div>
              <div className="text-[11px] text-slate-500">{step.desc}</div>
            </div>
            {i < steps.length - 1 && (
              <ArrowRight className="ml-auto hidden h-4 w-4 shrink-0 text-slate-300 sm:block" />
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
