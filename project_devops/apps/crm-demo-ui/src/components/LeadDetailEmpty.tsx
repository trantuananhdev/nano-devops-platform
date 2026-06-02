import { Inbox, MousePointerClick } from "lucide-react";
import { VI } from "../lib/vi";

type Props = {
  compact?: boolean;
};

export default function LeadDetailEmpty({ compact }: Props) {
  return (
    <div
      className={
        compact
          ? "flex flex-col items-center justify-center px-6 py-10 text-center"
          : "flex flex-col items-center justify-center px-8 py-14 text-center"
      }
    >
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-purple-50 text-purple-600">
        <Inbox className="h-7 w-7" />
      </div>
      <p className="text-sm font-semibold text-slate-800">{VI.detail.emptyTitle}</p>
      <p className="mt-2 max-w-xs text-xs leading-relaxed text-slate-500">
        {VI.detail.emptyHint}
      </p>
      <div className="mt-4 flex items-center gap-1.5 text-[11px] font-medium text-purple-700">
        <MousePointerClick className="h-3.5 w-3.5" />
        {VI.detail.emptyAction}
      </div>
    </div>
  );
}
