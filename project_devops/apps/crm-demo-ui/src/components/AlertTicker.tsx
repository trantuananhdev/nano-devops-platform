import { AlertTriangle } from "lucide-react";
import type { Lead } from "../types";
import { VI, intentVi } from "../lib/vi";

type Props = { alerts: Lead[] };

export default function AlertTicker({ alerts }: Props) {
  return (
    <div className="flex h-full min-h-[200px] flex-col rounded-2xl border border-red-200/80 bg-gradient-to-b from-red-50 to-white p-4 shadow-sm">
      <h3 className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase text-red-800">
        <AlertTriangle className="h-4 w-4" />
        {VI.alerts.title}
      </h3>
      <p className="mb-3 text-[11px] text-red-700/80">
        Lead khẩn cần gọi trong SLA — ưu tiên trước inbox thường
      </p>
      {alerts.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-red-200 bg-white/60 px-4 py-8 text-center">
          <p className="text-xs text-slate-500">{VI.alerts.empty}</p>
        </div>
      ) : (
        <ul className="max-h-52 flex-1 space-y-2 overflow-y-auto text-xs">
          {alerts.map((a) => (
            <li
              key={a.message_id}
              className="rounded-xl border border-red-100 bg-white px-3 py-2 shadow-sm"
            >
              <div className="font-semibold text-red-900">
                {VI.channels[a.channel as keyof typeof VI.channels] || a.channel}
                <span className="font-normal text-red-700"> · {intentVi(a.intent)}</span>
              </div>
              <p className="mt-1 line-clamp-2 text-slate-600">
                {a.summary || a.raw_text || "—"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
