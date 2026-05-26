import type { Lead } from "../types";
import { VI, intentVi } from "../lib/vi";

type Props = { alerts: Lead[] };

export default function AlertTicker({ alerts }: Props) {
  return (
    <div className="rounded-lg border border-red-900/60 bg-red-950/30 p-2">
      <h3 className="mb-1 text-xs font-semibold uppercase text-red-400">{VI.alerts.title}</h3>
      {alerts.length === 0 ? (
        <p className="text-xs text-slate-500">{VI.alerts.empty}</p>
      ) : (
        <ul className="max-h-24 space-y-1 overflow-y-auto text-xs">
          {alerts.map((a) => (
            <li key={a.message_id} className="animate-pulse text-red-200">
              🚨 {VI.channels[a.channel as keyof typeof VI.channels] || a.channel} ·{" "}
              {intentVi(a.intent)} · {a.summary?.slice(0, 70)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
