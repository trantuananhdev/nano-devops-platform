import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  connectLeadStream,
  demoSend,
  demoTrafficBurst,
  fetchAlerts,
  fetchLead,
  fetchLeads,
  fetchMetrics,
  fetchScenarios,
} from "./api/client";
import AiCapabilities from "./components/AiCapabilities";
import AlertTicker from "./components/AlertTicker";
import ChannelButtons from "./components/ChannelButtons";
import CrmPipeline from "./components/CrmPipeline";
import LeadDetail from "./components/LeadDetail";
import LeadStream from "./components/LeadStream";
import MetricsBar from "./components/MetricsBar";
import MultiChannelHub from "./components/MultiChannelHub";
import RoiCalculator from "./components/RoiCalculator";
import TrafficScenarios from "./components/TrafficScenarios";
import { FALLBACK_SCENARIOS } from "./data/fallbackScenarios";
import { VI } from "./lib/vi";
import type { ChannelId, Lead, LeadEvent, TrafficScenario } from "./types";

function eventToLead(ev: LeadEvent): Lead {
  const stage =
    ev.type === "lead_queued"
      ? "queued"
      : ev.type === "lead_processing"
        ? "processing"
        : ev.processed_at
          ? "done"
          : "processing";

  return {
    message_id: ev.message_id,
    channel: ev.channel,
    raw_text: ev.raw_text,
    customer_name: ev.customer_name,
    phone: ev.phone,
    product_interest: ev.product_interest,
    language: ev.language,
    order_id: ev.order_id,
    shop_id: ev.shop_id,
    locale: ev.locale,
    urgency: ev.urgency === "pending" ? "medium" : ev.urgency,
    sentiment: ev.sentiment === "pending" ? "neutral" : ev.sentiment,
    intent: ev.intent,
    summary: ev.summary,
    alert_sent: ev.alert_sent,
    auto_reply_sent: ev.auto_reply_sent,
    auto_reply_content: ev.auto_reply_content,
    processed_at: ev.processed_at,
    pipeline_stage: stage,
  };
}

function statusFromEvent(ev: LeadEvent): string {
  switch (ev.type) {
    case "lead_queued":
      return ev.queue_depth && ev.queue_depth > 1
        ? VI.status.queuedDepth(ev.queue_depth)
        : VI.status.queued;
    case "lead_processing":
      return VI.status.processing;
    case "auto_reply_sent":
      return VI.status.autoReply;
    case "lead_processed":
      return VI.status.processed;
    default:
      return VI.status.live;
  }
}

export default function App() {
  const qc = useQueryClient();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState(false);
  const [status, setStatus] = useState(VI.status.connecting);
  const [activeScenario, setActiveScenario] = useState<TrafficScenario | null>(null);
  const [aiFocus, setAiFocus] = useState<string | undefined>();
  const pendingRef = useRef<Set<string>>(new Set());

  const {
    data: scenariosFromApi,
    isError: scenariosApiError,
    isLoading: scenariosLoading,
  } = useQuery({
    queryKey: ["scenarios"],
    queryFn: fetchScenarios,
    staleTime: 60_000,
    retry: 1,
  });

  const scenarios =
    scenariosFromApi && scenariosFromApi.length > 0
      ? scenariosFromApi
      : scenariosApiError || (!scenariosLoading && !scenariosFromApi?.length)
        ? FALLBACK_SCENARIOS
        : [];

  const { data: initialLeads } = useQuery({ queryKey: ["leads"], queryFn: () => fetchLeads(50) });
  const { data: metrics } = useQuery({
    queryKey: ["metrics"],
    queryFn: fetchMetrics,
    refetchInterval: 8_000,
  });
  const { data: alerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
    refetchInterval: 6_000,
  });
  const { data: selectedLead, isFetching: detailLoading } = useQuery({
    queryKey: ["lead", selectedId],
    queryFn: () => fetchLead(selectedId!),
    enabled: !!selectedId,
  });

  useEffect(() => {
    if (initialLeads) {
      setLeads(initialLeads.map((l) => ({ ...l, pipeline_stage: "done" as const })));
    }
  }, [initialLeads]);

  const mergeLead = useCallback((incoming: Lead) => {
    setLeads((prev) => {
      const idx = prev.findIndex((p) => p.message_id === incoming.message_id);
      if (idx < 0) return [incoming, ...prev].slice(0, 80);
      const existing = prev[idx];
      const merged: Lead = {
        ...existing,
        ...incoming,
        raw_text: incoming.raw_text || existing.raw_text,
        customer_name: incoming.customer_name || existing.customer_name,
        phone: incoming.phone || existing.phone,
        product_interest: incoming.product_interest || existing.product_interest,
        order_id: incoming.order_id || existing.order_id,
        summary: incoming.summary || existing.summary,
        auto_reply_content: incoming.auto_reply_content || existing.auto_reply_content,
        processed_at: incoming.processed_at || existing.processed_at,
        alert_sent: incoming.alert_sent ?? existing.alert_sent,
        auto_reply_sent: incoming.auto_reply_sent ?? existing.auto_reply_sent,
        pipeline_stage:
          incoming.processed_at || incoming.pipeline_stage === "done"
            ? "done"
            : incoming.pipeline_stage || existing.pipeline_stage,
      };
      if (incoming.intent !== "queued" && incoming.intent !== "processing") {
        merged.pipeline_stage = "done";
      }
      const rest = prev.filter((_, i) => i !== idx);
      return [merged, ...rest];
    });
  }, []);

  const handleStreamEvent = useCallback(
    (ev: LeadEvent) => {
      setLive(true);
      setStatus(statusFromEvent(ev));
      mergeLead(eventToLead(ev));

      if (ev.type === "lead_queued" || ev.type === "lead_processing") {
        pendingRef.current.add(ev.message_id);
      }
      if (ev.type === "lead_processed") {
        pendingRef.current.delete(ev.message_id);
        qc.invalidateQueries({ queryKey: ["metrics"] });
        qc.invalidateQueries({ queryKey: ["alerts"] });
      }
      if (ev.type === "auto_reply_sent") {
        qc.invalidateQueries({ queryKey: ["metrics"] });
      }
      if (selectedId === ev.message_id) {
        qc.invalidateQueries({ queryKey: ["lead", ev.message_id] });
      }
    },
    [mergeLead, qc, selectedId]
  );

  useEffect(() => {
    const close = connectLeadStream(handleStreamEvent);
    let timer: ReturnType<typeof setTimeout>;

    const poll = () => {
      fetchLeads(50)
        .then((rows) => {
          setLeads((prev) => {
            const byId = new Map(prev.map((l) => [l.message_id, l]));
            for (const row of rows) {
              const existing = byId.get(row.message_id);
              byId.set(row.message_id, {
                ...existing,
                ...row,
                pipeline_stage: "done",
                raw_text: row.raw_text ?? existing?.raw_text,
                customer_name: row.customer_name ?? existing?.customer_name,
              });
              pendingRef.current.delete(row.message_id);
            }
            return [...byId.values()].sort((a, b) => {
              const ta = a.processed_at ? Date.parse(a.processed_at) : 0;
              const tb = b.processed_at ? Date.parse(b.processed_at) : 0;
              return tb - ta;
            });
          });
          if (pendingRef.current.size === 0) {
            setStatus((s) => (s.startsWith("Lỗi") ? s : VI.status.live));
          }
        })
        .catch(() => setStatus(VI.status.pollFallback))
        .finally(() => {
          timer = setTimeout(poll, pendingRef.current.size > 0 ? 1500 : 5000);
        });
    };

    poll();
    return () => {
      close();
      clearTimeout(timer);
    };
  }, [handleStreamEvent]);

  const activeChannels = [
    ...new Set(leads.map((l) => l.channel as ChannelId)),
  ] as ChannelId[];

  const onSendChannel = async (
    channel: string,
    templateId?: string,
    category?: string
  ) => {
    setBusy(true);
    setStatus(`Đang gửi tin ${VI.channels[channel as keyof typeof VI.channels] || channel}…`);
    try {
      const res = await demoSend(channel, templateId, category);
      if (res.duplicate) {
        setStatus(VI.status.duplicate);
        return;
      }
      const mid = res.message_id || res.job_id;
      setSelectedId(mid);
      pendingRef.current.add(mid);
      setStatus(VI.status.queued);
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    } catch (e) {
      setStatus(`Lỗi: ${e instanceof Error ? e.message : "gửi tin thất bại"}`);
    } finally {
      setBusy(false);
    }
  };

  const onBurst = async (scenario: TrafficScenario) => {
    setBusy(true);
    setActiveScenario(scenario);
    setAiFocus(scenario.ai_focus_vi);
    setStatus(VI.status.sending(scenario.title_vi));
    try {
      const res = await demoTrafficBurst(scenario.id);
      if (res.message_ids?.length) {
        setSelectedId(res.message_ids[0]);
        res.message_ids.forEach((id) => pendingRef.current.add(id));
      }
      setStatus(VI.status.burstDone(res.accepted_count));
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    } catch (e) {
      setStatus(`Lỗi: ${e instanceof Error ? e.message : "đổ traffic thất bại"}`);
    } finally {
      setBusy(false);
    }
  };

  const detail =
    selectedLead ||
    (selectedId ? leads.find((l) => l.message_id === selectedId) ?? null : null);

  const hasPending = leads.some(
    (l) => l.pipeline_stage === "queued" || l.pipeline_stage === "processing"
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <header className="border-b border-slate-800 px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-bold text-amber-400">{VI.appTitle}</h1>
            <p className="max-w-2xl text-xs text-slate-500">{VI.appSubtitle}</p>
          </div>
          <div className="text-sm">
            <span className={live ? "text-emerald-400" : "text-amber-400"}>
              {hasPending ? "🔄" : live ? "🟢" : "🟡"} {status}
            </span>
          </div>
        </div>
        <div className="mt-3">
          <MetricsBar metrics={metrics} />
        </div>
        <div className="mt-3">
          <MultiChannelHub metrics={metrics} activeChannels={activeChannels} />
        </div>
      </header>

      <main className="grid gap-4 p-4 xl:grid-cols-[260px_1fr_260px]">
        <aside className="space-y-4">
          <TrafficScenarios
            scenarios={scenarios}
            activeId={activeScenario?.id ?? null}
            busy={busy}
            apiError={scenariosApiError}
            onBurst={onBurst}
          />
          <ChannelButtons onSend={onSendChannel} busy={busy} />
          <CrmPipeline />
          <RoiCalculator />
        </aside>

        <section className="flex min-h-[520px] flex-col gap-4">
          <LeadStream leads={leads} selectedId={selectedId} onSelect={setSelectedId} />
          <div className="grid gap-4 md:grid-cols-2">
            <LeadDetail lead={detail} loading={detailLoading && !!selectedId} />
            <AlertTicker alerts={alerts ?? []} />
          </div>
        </section>

        <aside className="hidden xl:block">
          <AiCapabilities focus={aiFocus} />
        </aside>
      </main>

      <div className="xl:hidden px-4 pb-4">
        <AiCapabilities focus={aiFocus} />
      </div>
    </div>
  );
}
