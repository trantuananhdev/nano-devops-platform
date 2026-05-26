import type { ChannelId, MetricsSummary } from "../types";
import { VI } from "../lib/vi";

const CHANNEL_META: Record<
  ChannelId,
  { label: string; color: string; border: string; icon: string }
> = {
  facebook: {
    label: VI.channels.facebook,
    color: "bg-blue-600/90",
    border: "border-blue-500",
    icon: "📘",
  },
  tiktok: {
    label: VI.channels.tiktok,
    color: "bg-pink-600/90",
    border: "border-pink-500",
    icon: "🎵",
  },
  shopee: {
    label: VI.channels.shopee,
    color: "bg-orange-500/90",
    border: "border-orange-500",
    icon: "🛍️",
  },
  generic: {
    label: VI.channels.generic,
    color: "bg-slate-600/90",
    border: "border-slate-500",
    icon: "💬",
  },
};

const HUB_CHANNELS: ChannelId[] = ["facebook", "tiktok", "shopee"];

type Props = {
  metrics?: MetricsSummary;
  activeChannels?: ChannelId[];
};

export default function MultiChannelHub({ metrics, activeChannels }: Props) {
  const byCh = metrics?.by_channel_24h ?? {};

  return (
    <div className="rounded-xl border border-amber-500/30 bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/20 p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-bold text-amber-300">{VI.multiChannel.title}</h2>
          <p className="text-[11px] text-slate-400">{VI.multiChannel.subtitle}</p>
        </div>
        <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
          MULTI-CHANNEL
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {HUB_CHANNELS.map((ch) => {
          const meta = CHANNEL_META[ch];
          const count = byCh[ch] ?? 0;
          const active = activeChannels?.includes(ch);
          return (
            <div
              key={ch}
              className={`rounded-lg border-2 px-2 py-2 text-center transition ${meta.border} ${
                active ? "ring-2 ring-amber-400 ring-offset-1 ring-offset-slate-900" : ""
              } ${meta.color}`}
            >
              <div className="text-lg">{meta.icon}</div>
              <div className="text-[11px] font-semibold text-white">{meta.label}</div>
              <div className="mt-1 text-[10px] text-white/80">
                {count > 0 ? `${count} tin/24h` : "Chờ traffic"}
              </div>
            </div>
          );
        })}
      </div>

      <p className="mt-2 text-center text-[10px] text-slate-500">
        Webhook → Redis → AI Worker → luồng tin bên dưới (một màn hình)
      </p>
    </div>
  );
}

export function ChannelChips({ channels }: { channels: ChannelId[] }) {
  if (!channels.length) return null;
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {channels.map((ch) => {
        const m = CHANNEL_META[ch] ?? CHANNEL_META.generic;
        return (
          <span
            key={ch}
            className={`rounded px-1.5 py-0.5 text-[9px] font-medium text-white ${m.color}`}
          >
            {m.icon} {m.label}
          </span>
        );
      })}
    </div>
  );
}
