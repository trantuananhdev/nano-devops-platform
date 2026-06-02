import { VI } from "../lib/vi";

type Props = {
  onSend: (channel: string, templateId?: string, category?: string) => void;
  busy: boolean;
};

const CHANNELS = [
  {
    id: "facebook",
    label: VI.channels.facebook,
    color: "bg-blue-600 hover:bg-blue-700",
    template: "apartment_price",
    category: "price_inquiry",
    desc: "Hỏi giá căn hộ",
  },
  {
    id: "zalo",
    label: "Zalo",
    color: "bg-blue-500 hover:bg-blue-600",
    template: "viewing_schedule",
    category: "schedule_viewing",
    desc: "Đặt lịch xem nhà",
  },
  {
    id: "tiktok",
    label: VI.channels.tiktok,
    color: "bg-slate-900 hover:bg-black",
    template: "apartment_inquiry",
    category: "inquiry",
    desc: "Tư vấn căn hộ",
  },
] as const;

export default function ChannelButtons({ onSend, busy }: Props) {
  return (
    <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        {VI.trafficPanel.singleTitle}
      </h2>
      <p className="text-[11px] text-slate-500">{VI.multiChannel.sendOne}</p>
      {CHANNELS.map((ch) => (
        <button
          key={ch.id}
          type="button"
          disabled={busy}
          onClick={() => onSend(ch.id, ch.template, ch.category)}
          className={`flex w-full flex-col rounded-xl px-3 py-2.5 text-left text-sm text-white transition disabled:opacity-50 ${ch.color}`}
        >
          <span className="font-semibold">{ch.label}</span>
          <span className="text-[10px] text-white/80">{ch.desc}</span>
        </button>
      ))}
    </div>
  );
}
