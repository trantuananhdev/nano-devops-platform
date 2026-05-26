import { VI } from "../lib/vi";

type Props = {
  onSend: (channel: string, templateId?: string, category?: string) => void;
  busy: boolean;
};

const CHANNELS = [
  {
    id: "facebook",
    label: VI.channels.facebook,
    color: "bg-blue-600 hover:bg-blue-500",
    template: "cancel_angry_tl",
    category: "cancel_order",
    desc: "Tagalog · hủy đơn → cảnh báo",
  },
  {
    id: "tiktok",
    label: VI.channels.tiktok,
    color: "bg-pink-600 hover:bg-pink-500",
    template: "price_serum_id",
    category: "inquiry",
    desc: "Bahasa · hỏi giá → auto-reply",
  },
  {
    id: "shopee",
    label: VI.channels.shopee,
    color: "bg-orange-500 hover:bg-orange-400",
    template: "shopee_delay_ms",
    category: "inquiry",
    desc: "Malay · tracking COD",
  },
  {
    id: "generic",
    label: VI.channels.generic,
    color: "bg-slate-600 hover:bg-slate-500",
    template: "urgent_sunscreen",
    category: "purchase",
    desc: "English · mua gấp",
  },
] as const;

export default function ChannelButtons({ onSend, busy }: Props) {
  return (
    <div className="space-y-2 rounded-lg border border-slate-700 bg-slate-900/40 p-2">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        {VI.trafficPanel.singleTitle}
      </h2>
      <p className="text-[10px] text-slate-500">{VI.multiChannel.sendOne}</p>
      {CHANNELS.map((ch) => (
        <button
          key={ch.id}
          type="button"
          disabled={busy}
          onClick={() => onSend(ch.id, ch.template, ch.category)}
          className={`flex w-full flex-col rounded-lg px-3 py-2 text-left text-sm text-white transition disabled:opacity-50 ${ch.color}`}
        >
          <span className="font-medium">{ch.label}</span>
          <span className="text-[10px] text-white/75">{ch.desc}</span>
        </button>
      ))}
    </div>
  );
}
