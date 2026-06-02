import { cn } from "../lib/utils";

type Props = {
  live: boolean;
  busy: boolean;
  hasPending: boolean;
  status: string;
  leadCount: number;
};

export default function StatusPill({ live, busy, hasPending, status, leadCount }: Props) {
  const tone = hasPending
    ? "bg-amber-50 text-amber-800 border-amber-200"
    : live
      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
      : busy
        ? "bg-blue-50 text-blue-800 border-blue-200"
        : "bg-slate-50 text-slate-700 border-slate-200";

  const dot = hasPending
    ? "bg-amber-500 live-dot"
    : live
      ? "bg-emerald-500 live-dot"
      : busy
        ? "bg-blue-500 animate-pulse"
        : "bg-slate-400";

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <span className="hidden rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 sm:inline-flex">
        {leadCount} lead trong phiên
      </span>
      <span
        className={cn(
          "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold",
          tone
        )}
      >
        <span className={cn("h-2 w-2 rounded-full", dot)} />
        {hasPending ? "AI đang xử lý hàng đợi…" : status}
      </span>
    </div>
  );
}
