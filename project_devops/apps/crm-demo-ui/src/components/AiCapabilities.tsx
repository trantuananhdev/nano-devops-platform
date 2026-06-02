import { VI } from "../lib/vi";

type Props = { focus?: string };

export default function AiCapabilities({ focus }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        {VI.ai.title}
      </h2>
      {focus && (
        <p className="mb-3 rounded-lg border border-purple-100 bg-purple-50 px-2.5 py-2 text-[11px] text-purple-800">
          Kịch bản vừa chọn: {focus}
        </p>
      )}
      <ul className="space-y-2.5">
        {VI.ai.items.map((item) => (
          <li key={item.title} className="flex gap-2 text-[11px]">
            <span>{item.icon}</span>
            <div>
              <div className="font-semibold text-slate-800">{item.title}</div>
              <div className="text-slate-500">{item.desc}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
