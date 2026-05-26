import type { Lead } from "../types";
import { VI, intentVi, sentimentVi, urgencyVi } from "../lib/vi";

type Props = { lead: Lead | null; loading?: boolean };

const LOCALE_LABEL: Record<string, string> = {
  "tl-PH": "Tagalog (Philippines)",
  "id-ID": "Bahasa Indonesia",
  "ms-MY": "Bahasa Malaysia",
  "en-US": "English",
};

export default function LeadDetail({ lead, loading }: Props) {
  if (loading) return <p className="text-sm text-slate-500">Đang tải hồ sơ khách…</p>;
  if (!lead) return <p className="text-sm text-slate-500">{VI.detail.empty}</p>;

  const inFlight =
    lead.pipeline_stage === "queued" || lead.pipeline_stage === "processing";

  return (
    <div className="space-y-3 text-sm">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        {VI.detail.title}
      </h2>

      {inFlight && (
        <p className="rounded border border-cyan-700/40 bg-cyan-950/30 px-2 py-1 text-xs text-cyan-300">
          {lead.pipeline_stage === "queued" ? VI.detail.waitingQueue : VI.detail.waitingAi}
        </p>
      )}

      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-3">
        <div className="text-[10px] uppercase text-slate-500">{VI.detail.customer}</div>
        <div className="mt-1 font-medium text-slate-100">
          {lead.customer_name || "— (AI trích xuất sau khi xử lý)"}
        </div>
        <dl className="mt-2 grid grid-cols-2 gap-2 text-xs">
          <div>
            <dt className="text-slate-500">{VI.detail.phone}</dt>
            <dd className="text-slate-200">{lead.phone || "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{VI.detail.order}</dt>
            <dd className="text-slate-200">{lead.order_id || "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">{VI.detail.channel}</dt>
            <dd className="text-slate-200">
              {VI.channels[lead.channel as keyof typeof VI.channels] || lead.channel}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">{VI.detail.locale}</dt>
            <dd className="text-slate-200">
              {lead.locale ? LOCALE_LABEL[lead.locale] || lead.locale : lead.language || "—"}
            </dd>
          </div>
          <div className="col-span-2">
            <dt className="text-slate-500">{VI.detail.product}</dt>
            <dd className="text-slate-200">{lead.product_interest || "—"}</dd>
          </div>
        </dl>
      </div>

      {lead.raw_text && (
        <div>
          <div className="text-[10px] uppercase text-slate-500">{VI.detail.message}</div>
          <p className="mt-1 rounded bg-slate-800/80 p-2 italic text-slate-200">{lead.raw_text}</p>
        </div>
      )}

      <p>
        <span className="text-slate-500">{VI.detail.summary}:</span> {lead.summary || "—"}
      </p>

      {!inFlight && (
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="rounded bg-slate-800 p-2">
            <div className="text-slate-500">{VI.detail.intent}</div>
            <div>{intentVi(lead.intent)}</div>
          </div>
          <div className="rounded bg-slate-800 p-2">
            <div className="text-slate-500">{VI.detail.urgency}</div>
            <div>{urgencyVi(lead.urgency)}</div>
          </div>
          <div className="rounded bg-slate-800 p-2">
            <div className="text-slate-500">{VI.detail.sentiment}</div>
            <div>{sentimentVi(lead.sentiment)}</div>
          </div>
        </div>
      )}

      {lead.auto_reply_sent && lead.auto_reply_content && (
        <div className="rounded-lg border border-emerald-700/50 bg-emerald-950/40 p-3">
          <div className="mb-1 text-xs font-semibold text-emerald-400">{VI.detail.autoReply}</div>
          <p className="text-slate-200">{lead.auto_reply_content}</p>
        </div>
      )}

      {lead.alert_sent && (
        <p className="text-xs text-red-400">{VI.detail.alert(lead.alert_type)}</p>
      )}
    </div>
  );
}
