import type { Lead } from "../types";
import { VI, intentVi, sentimentVi, urgencyVi } from "../lib/vi";

type Props = {
  leads: Lead[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

function urgencyClass(u: string, stage?: Lead["pipeline_stage"]) {
  if (stage === "queued" || stage === "processing") {
    return "border-l-4 border-cyan-500 bg-cyan-950/20 animate-pulse";
  }
  if (u === "critical" || u === "high") return "border-l-4 border-red-500 bg-red-950/30";
  if (u === "medium") return "border-l-4 border-amber-500";
  return "border-l-4 border-slate-600";
}

export default function LeadStream({ leads, selectedId, onSelect }: Props) {
  return (
    <div className="flex h-full flex-col">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {VI.stream.title}
      </h2>
      <div className="min-h-0 flex-1 overflow-y-auto rounded-lg border border-slate-700 bg-slate-900/50">
        {leads.length === 0 ? (
          <p className="p-4 text-sm text-slate-500">{VI.stream.empty}</p>
        ) : (
          <ul>
            {leads.map((lead) => (
              <li key={lead.message_id}>
                <button
                  type="button"
                  onClick={() => onSelect(lead.message_id)}
                  className={`w-full px-3 py-2 text-left text-sm transition hover:bg-slate-800 ${urgencyClass(
                    lead.urgency,
                    lead.pipeline_stage
                  )} ${selectedId === lead.message_id ? "ring-1 ring-amber-400" : ""}`}
                >
                  <div className="flex justify-between gap-2">
                    <span className="font-medium text-amber-300">
                      {VI.channels[lead.channel as keyof typeof VI.channels] || lead.channel}
                    </span>
                    <span className="text-xs text-slate-500">
                      {lead.processed_at
                        ? new Date(lead.processed_at).toLocaleTimeString("vi-VN")
                        : lead.pipeline_stage === "queued"
                          ? VI.stream.queued
                          : lead.pipeline_stage === "processing"
                            ? VI.stream.processing
                            : "…"}
                    </span>
                  </div>
                  {lead.customer_name && (
                    <div className="text-xs text-slate-300">{lead.customer_name}</div>
                  )}
                  <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-400">
                    {lead.pipeline_stage === "done" ? (
                      <>
                        <span>{intentVi(lead.intent)}</span>
                        <span>·</span>
                        <span>{urgencyVi(lead.urgency)}</span>
                        <span>·</span>
                        <span>{sentimentVi(lead.sentiment)}</span>
                      </>
                    ) : (
                      <span className="text-slate-500">{lead.summary || VI.stream.waiting}</span>
                    )}
                    {lead.alert_sent && <span className="text-red-400">🚨</span>}
                    {lead.auto_reply_sent && <span className="text-emerald-400">💬</span>}
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
