import type { ChannelId, MetricsSummary } from "../types";
import { VI } from "../lib/vi";
import { cn } from "../lib/utils";

const CHANNEL_META: Record<
  ChannelId,
  { label: string; color: string; border: string; icon: string }
> = {
  facebook: {
    label: VI.channels.facebook,
    color: "bg-blue-600",
    border: "border-blue-200",
    icon: "📘",
  },
  tiktok: {
    label: VI.channels.tiktok,
    color: "bg-slate-900",
    border: "border-slate-300",
    icon: "🎵",
  },
  zalo: {
    label: "Zalo",
    color: "bg-blue-500",
    border: "border-blue-200",
    icon: "💬",
  },
  shopee: {
    label: VI.channels.shopee,
    color: "bg-orange-500",
    border: "border-orange-200",
    icon: "🛍️",
  },
  instagram: {
    label: "Instagram",
    color: "bg-gradient-to-br from-purple-500 to-pink-500",
    border: "border-pink-200",
    icon: "📷",
  },
  generic: {
    label: VI.channels.generic,
    color: "bg-slate-600",
    border: "border-slate-200",
    icon: "💬",
  },
};

const HUB_CHANNELS: ChannelId[] = ["facebook", "zalo", "tiktok"];

type Props = {
  metrics?: MetricsSummary;
  activeChannels?: ChannelId[];
};

export default function MultiChannelHub({ metrics, activeChannels }: Props) {
  const byCh = metrics?.by_channel_24h ?? {};

  return (
    <div className="rounded-xl border border-slate-200 bg-gradient-to-br from-white via-purple-50/30 to-white p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-bold text-slate-900">{VI.multiChannel.title}</h2>
          <p className="text-[11px] text-slate-500">{VI.multiChannel.subtitle}</p>
        </div>
        <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-700">
          LIVE
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
              className={cn(
                "rounded-xl border-2 bg-white px-2 py-2.5 text-center transition",
                meta.border,
                active && "ring-2 ring-purple-400 ring-offset-1"
              )}
            >
              <div className="text-lg">{meta.icon}</div>
              <div className="text-[11px] font-semibold text-slate-800">{meta.label}</div>
              <div
                className={cn(
                  "mt-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-medium text-white",
                  meta.color
                )}
              >
                {count > 0 ? `${count} tin/24h` : "Chờ traffic"}
              </div>
            </div>
          );
        })}
      </div>

      <p className="mt-2 text-center text-[10px] text-slate-400">
        Webhook → Redis → AI Worker → luồng tin bên dưới
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
            className={cn(
              "rounded-md px-1.5 py-0.5 text-[9px] font-medium text-white",
              m.color
            )}
          >
            {m.icon} {m.label}
          </span>
        );
      })}
    </div>
  );
}
