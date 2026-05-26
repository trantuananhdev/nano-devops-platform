import type { MetricsSummary } from "../types";
import { VI } from "../lib/vi";

type Props = { metrics: MetricsSummary | undefined };

export default function MetricsBar({ metrics }: Props) {
  if (!metrics) return null;
  const cards = [
    { label: VI.metrics.processed1h, value: metrics.processed_1h },
    { label: VI.metrics.processed24h, value: metrics.processed_24h },
    { label: VI.metrics.alerts24h, value: metrics.alerts_24h },
    { label: VI.metrics.autoReplies, value: metrics.auto_replies_24h },
    { label: VI.metrics.hot1h, value: metrics.hot_leads_1h },
  ];
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      {cards.map((c) => (
        <div key={c.label} className="rounded-lg bg-slate-800/80 px-3 py-2">
          <div className="text-[10px] uppercase text-slate-500">{c.label}</div>
          <div className="text-lg font-semibold text-amber-300">{c.value}</div>
        </div>
      ))}
    </div>
  );
}
