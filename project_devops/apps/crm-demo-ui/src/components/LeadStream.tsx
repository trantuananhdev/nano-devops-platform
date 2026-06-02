import { Inbox, Loader2 } from "lucide-react";
import type { Lead } from "../types";
import { VI, intentVi, sentimentVi, urgencyVi } from "../lib/vi";
import { KANBAN_STAGE_LABELS } from "../lib/crm-labels";
import { cn } from "../lib/utils";
import { Badge } from "./ui/badge";

type Props = {
  leads: Lead[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

function urgencyClass(u: string, stage?: Lead["pipeline_stage"]) {
  if (stage === "queued" || stage === "processing") {
    return "border-l-4 border-cyan-500 bg-cyan-50/90";
  }
  if (u === "critical" || u === "high") return "border-l-4 border-red-500 bg-red-50/80";
  if (u === "medium") return "border-l-4 border-amber-400 bg-amber-50/50";
  return "border-l-4 border-slate-200 bg-white";
}

function pipelineBadge(stage?: Lead["pipeline_stage"]) {
  if (stage === "queued") return <Badge variant="blue">{VI.stream.queued}</Badge>;
  if (stage === "processing") return <Badge variant="warning">{VI.stream.processing}</Badge>;
  return null;
}

export default function LeadStream({ leads, selectedId, onSelect }: Props) {
  return (
    <div className="flex min-h-[320px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {VI.stream.title}
          </h2>
          <p className="text-[11px] text-slate-400">{VI.stream.count(leads.length)}</p>
        </div>
        {leads.some(
          (l) => l.pipeline_stage === "queued" || l.pipeline_stage === "processing"
        ) && (
          <span className="flex items-center gap-1 text-[10px] font-medium text-cyan-700">
            <Loader2 className="h-3 w-3 animate-spin" />
            AI
          </span>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {leads.length === 0 ? (
          <div className="flex flex-col items-center px-6 py-12 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-400">
              <Inbox className="h-6 w-6" />
            </div>
            <p className="text-sm font-medium text-slate-700">{VI.stream.empty}</p>
            <p className="mt-2 max-w-xs text-xs leading-relaxed text-slate-500">
              {VI.stream.emptyHint}
            </p>
          </div>
        ) : (
          <ul>
            {leads.map((lead) => (
              <li key={lead.message_id} className="border-b border-slate-100 last:border-0">
                <button
                  type="button"
                  onClick={() => onSelect(lead.message_id)}
                  className={cn(
                    "lead-row w-full px-4 py-3 text-left text-sm transition",
                    urgencyClass(lead.urgency, lead.pipeline_stage),
                    selectedId === lead.message_id &&
                      "selected bg-purple-50 ring-1 ring-inset ring-purple-200"
                  )}
                >
                  <div className="flex justify-between gap-2">
                    <span className="font-semibold text-slate-900">
                      {VI.channels[lead.channel as keyof typeof VI.channels] ||
                        lead.channel}
                    </span>
                    <span className="shrink-0 text-xs text-slate-500">
                      {lead.processed_at
                        ? new Date(lead.processed_at).toLocaleTimeString("vi-VN", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : "—"}
                    </span>
                  </div>
                  <div className="mt-0.5 truncate text-xs font-medium text-slate-700">
                    {lead.customer_name || "Khách ẩn danh"}
                  </div>
                  {lead.location && (
                    <div className="mt-0.5 truncate text-[11px] text-slate-500">
                      {lead.location}
                      {lead.property_type ? ` · ${lead.property_type}` : ""}
                    </div>
                  )}
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    {pipelineBadge(lead.pipeline_stage)}
                    {lead.kanban_stage && lead.pipeline_stage === "done" && (
                      <Badge variant="outline">
                        {KANBAN_STAGE_LABELS[lead.kanban_stage] || lead.kanban_stage}
                      </Badge>
                    )}
                    {lead.pipeline_stage === "done" ? (
                      <>
                        <span className="text-[11px] text-slate-500">
                          {intentVi(lead.intent)}
                        </span>
                        <span className="text-slate-300">·</span>
                        <span className="text-[11px] text-slate-500">
                          {urgencyVi(lead.urgency)}
                        </span>
                        <span className="text-slate-300">·</span>
                        <span className="text-[11px] text-slate-500">
                          {sentimentVi(lead.sentiment)}
                        </span>
                      </>
                    ) : (
                      <span className="line-clamp-1 text-[11px] text-slate-500">
                        {lead.summary || VI.stream.waiting}
                      </span>
                    )}
                    {lead.alert_sent && (
                      <Badge variant="danger">Khẩn</Badge>
                    )}
                    {lead.auto_reply_sent && (
                      <Badge variant="success">Đã trả lời</Badge>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
