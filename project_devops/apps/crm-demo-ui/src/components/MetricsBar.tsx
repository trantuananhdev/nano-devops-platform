import { Bell, Flame, MessageSquare, Zap } from "lucide-react";
import type { MetricsSummary } from "../types";
import { VI } from "../lib/vi";
import { cn } from "../lib/utils";

type Props = { metrics: MetricsSummary | undefined };

const ICONS = [Zap, MessageSquare, Bell, MessageSquare, Flame] as const;

export default function MetricsBar({ metrics }: Props) {
  if (!metrics) {
    return (
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-[72px] animate-pulse rounded-xl border border-slate-200 bg-white"
          />
        ))}
      </div>
    );
  }

  const cards = [
    { label: VI.metrics.processed1h, value: metrics.processed_1h, accent: "text-violet-700" },
    { label: VI.metrics.processed24h, value: metrics.processed_24h, accent: "text-slate-800" },
    { label: VI.metrics.alerts24h, value: metrics.alerts_24h, accent: "text-red-600" },
    { label: VI.metrics.autoReplies, value: metrics.auto_replies_24h, accent: "text-emerald-700" },
    { label: VI.metrics.hot1h, value: metrics.hot_leads_1h, accent: "text-orange-600" },
  ];

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      {cards.map((c, i) => {
        const Icon = ICONS[i] ?? Zap;
        return (
          <div
            key={c.label}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm transition hover:border-purple-200 hover:shadow-md"
          >
            <div className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wide text-slate-500">
              <Icon className="h-3 w-3 opacity-70" />
              {c.label}
            </div>
            <div className={cn("mt-1 text-xl font-bold tabular-nums", c.accent)}>
              {c.value}
            </div>
          </div>
        );
      })}
    </div>
  );
}
