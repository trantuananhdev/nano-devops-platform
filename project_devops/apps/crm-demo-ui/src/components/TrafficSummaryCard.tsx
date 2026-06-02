import { BarChart3, Loader2, Sparkles } from "lucide-react";
import type { TrafficSummary } from "../types";
import { CHANNEL_LABELS } from "../lib/crm-labels";
import { VI } from "../lib/vi";

type Props = {
  summary: TrafficSummary | null;
  loading?: boolean;
};

export default function TrafficSummaryCard({ summary, loading }: Props) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 bg-gradient-to-r from-orange-50/80 via-white to-purple-50/50 px-4 py-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-2">
            <div className="rounded-lg bg-orange-100 p-2 text-orange-700">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {VI.trafficSummary.title}
              </div>
              <div className="mt-0.5 text-base font-semibold text-slate-900">
                {summary?.title_vi || VI.trafficSummary.empty}
              </div>
            </div>
          </div>
          <div className="rounded-xl border border-orange-200 bg-orange-50 px-4 py-2 text-center min-w-[88px]">
            <div className="text-[10px] font-semibold uppercase text-orange-800">
              {VI.trafficSummary.hotLeads}
            </div>
            <div className="text-2xl font-bold tabular-nums text-orange-700">
              {summary ? summary.hot_leads : loading ? "…" : "0"}
            </div>
          </div>
        </div>
      </div>

      <div className="p-4">
        {loading && !summary ? (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Loader2 className="h-4 w-4 animate-spin text-purple-600" />
            {VI.trafficSummary.loading}
          </div>
        ) : summary ? (
          <>
            <p className="text-sm leading-relaxed text-slate-700">{summary.summary_vi}</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-3">
                <div className="text-xs font-semibold text-slate-600">
                  {VI.trafficSummary.channels}
                </div>
                <div className="mt-2 space-y-1.5 text-xs">
                  {Object.entries(summary.channels || {}).length === 0 ? (
                    <div className="text-slate-400">—</div>
                  ) : (
                    Object.entries(summary.channels || {}).map(([ch, n]) => (
                      <div key={ch} className="flex items-center justify-between gap-2">
                        <span className="font-medium text-slate-800">
                          {CHANNEL_LABELS[ch] || ch}
                        </span>
                        <span className="tabular-nums rounded-full bg-white px-2 py-0.5 font-semibold text-slate-600 shadow-sm">
                          {n}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-3">
                <div className="flex items-center gap-1 text-xs font-semibold text-slate-600">
                  <Sparkles className="h-3.5 w-3.5 text-purple-600" />
                  {VI.trafficSummary.recommendations}
                </div>
                <ul className="mt-2 list-none space-y-2 text-xs text-slate-700">
                  {(summary.recommendations || []).slice(0, 4).map((r, idx) => (
                    <li
                      key={idx}
                      className="flex gap-2 rounded-lg border border-purple-100/80 bg-white px-2 py-1.5"
                    >
                      <span className="font-bold text-purple-600">{idx + 1}.</span>
                      <span>{r}</span>
                    </li>
                  ))}
                  {(summary.recommendations || []).length === 0 && (
                    <li className="text-slate-400">—</li>
                  )}
                </ul>
              </div>
            </div>
          </>
        ) : (
          <p className="text-sm text-slate-500">{VI.trafficSummary.emptyHint}</p>
        )}
      </div>
    </div>
  );
}
