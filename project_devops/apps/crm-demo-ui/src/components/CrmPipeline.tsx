import { VI } from "../lib/vi";

export default function CrmPipeline() {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {VI.pipeline.title}
      </h2>
      <ol className="space-y-2">
        {VI.pipeline.steps.map((step) => (
          <li key={step.id} className="flex gap-2 text-[11px]">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-400">
              {step.id}
            </span>
            <div>
              <div className="font-medium text-slate-200">{step.label}</div>
              <div className="text-slate-500">{step.desc}</div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
