import { VI } from "../lib/vi";

type Props = { focus?: string };

export default function AiCapabilities({ focus }: Props) {
  return (
    <div className="rounded-lg border border-emerald-900/40 bg-emerald-950/20 p-3">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
        {VI.ai.title}
      </h2>
      {focus && (
        <p className="mb-2 rounded bg-emerald-900/30 px-2 py-1 text-[10px] text-emerald-200">
          Kịch bản vừa chọn: {focus}
        </p>
      )}
      <ul className="space-y-2">
        {VI.ai.items.map((item) => (
          <li key={item.title} className="flex gap-2 text-[11px]">
            <span>{item.icon}</span>
            <div>
              <div className="font-medium text-slate-200">{item.title}</div>
              <div className="text-slate-500">{item.desc}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
