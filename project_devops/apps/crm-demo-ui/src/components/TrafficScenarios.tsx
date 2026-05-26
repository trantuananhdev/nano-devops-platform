import type { TrafficScenario } from "../types";
import { ChannelChips } from "./MultiChannelHub";
import { VI } from "../lib/vi";

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
    <div className="space-y-2">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        {VI.trafficPanel.title}
      </h2>
      <p className="text-[10px] leading-snug text-slate-500">{VI.trafficPanel.hint}</p>

      {apiError && (
        <p className="rounded border border-amber-700/50 bg-amber-950/30 px-2 py-1 text-[10px] text-amber-200">
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
              className={`w-full rounded-lg border px-3 py-2 text-left transition disabled:opacity-50 ${
                activeId === s.id
                  ? "border-amber-500 bg-amber-950/40"
                  : s.id === "multi_channel_mix"
                    ? "border-cyan-600/60 bg-cyan-950/30 hover:border-cyan-500"
                    : "border-slate-700 bg-slate-900/60 hover:border-slate-500"
              }`}
            >
              <div className="flex items-start gap-2">
                <span className="text-lg">{s.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-amber-200">{s.title_vi}</div>
                  <ChannelChips channels={s.channels ?? []} />
                  <div className="mt-1 text-[10px] text-slate-400 line-clamp-2">
                    {s.description_vi}
                  </div>
                  <div className="mt-0.5 text-[10px] text-slate-500">
                    {s.message_count} tin · ~{Math.round((s.message_count * s.delay_ms) / 1000)}s
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
