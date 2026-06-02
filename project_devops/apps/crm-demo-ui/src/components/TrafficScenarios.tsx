import type { TrafficScenario } from "../types";
import { ChannelChips } from "./MultiChannelHub";
import { VI } from "../lib/vi";
import { cn } from "../lib/utils";

type Props = {
  scenarios: TrafficScenario[];
  activeId: string | null;
  busy: boolean;
  apiError?: boolean;
  onBurst: (scenario: TrafficScenario) => void;
};

export default function TrafficScenarios({
  scenarios,
  activeId,
  busy,
  apiError,
  onBurst,
}: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {VI.trafficPanel.title}
        </h2>
        <p className="mt-1 text-[11px] leading-snug text-slate-500">{VI.trafficPanel.hint}</p>
        <p className="mt-2 rounded-lg bg-purple-50 px-2 py-1 text-[10px] font-medium text-purple-800">
          Khuyến nghị: bắt đầu bằng kịch bản đa kênh ★
        </p>
      </div>

      {apiError && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-2 py-1.5 text-[11px] text-amber-800">
          {VI.multiChannel.emptyScenarios}
        </p>
      )}

      {scenarios.length === 0 ? (
        <p className="text-xs text-slate-500">Đang tải kịch bản…</p>
      ) : (
        <div className="space-y-2">
          {scenarios.map((s) => (
            <button
              key={s.id}
              type="button"
              disabled={busy}
              onClick={() => onBurst(s)}
              className={cn(
                "w-full rounded-xl border px-3 py-2.5 text-left transition disabled:opacity-50",
                activeId === s.id
                  ? "border-purple-500 bg-purple-50 shadow-sm ring-1 ring-purple-200"
                  : "border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-white"
              )}
            >
              <div className="flex items-start gap-2">
                <span className="text-lg">{s.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold text-slate-900">{s.title_vi}</div>
                  <ChannelChips channels={s.channels ?? []} />
                  <div className="mt-1 text-[11px] text-slate-600 line-clamp-2">
                    {s.description_vi}
                  </div>
                  <div className="mt-0.5 text-[10px] text-slate-400">
                    {Math.min(s.message_count, 3)} tin · ~{Math.round((Math.min(s.message_count, 3) * s.delay_ms) / 1000)}s
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
