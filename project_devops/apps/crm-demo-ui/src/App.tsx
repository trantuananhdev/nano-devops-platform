import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  Building2,
  LayoutDashboard,
  KanbanSquare,
  User,
  Activity as ActivityIcon,
  Briefcase,
  Phone,
  Mail,
  Calendar,
  TrendingUp,
  Tag,
  Globe,
  Map as MapIcon,
  Bot,
  Plus,
  GripVertical,
  Flag,
} from "lucide-react";
import {
  connectLeadStream,
  demoSend,
  demoTrafficBurst,
  fetchAlerts,
  fetchLead,
  fetchLeads,
  fetchMetrics,
  fetchScenarios,
  updateLeadStage,
  fetchActivities,
  createActivity,
  fetchDeals,
  createDeal,
  fetchTrafficSummary,
} from "./api/client";
import AiCapabilities from "./components/AiCapabilities";
import AlertTicker from "./components/AlertTicker";
import ChannelButtons from "./components/ChannelButtons";
import LeadStream from "./components/LeadStream";
import MetricsBar from "./components/MetricsBar";
import MultiChannelHub from "./components/MultiChannelHub";
import RoiCalculator from "./components/RoiCalculator";
import TrafficScenarios from "./components/TrafficScenarios";
import TrafficSummaryCard from "./components/TrafficSummaryCard";
import DemoWorkflowBanner from "./components/DemoWorkflowBanner";
import LeadDetailEmpty from "./components/LeadDetailEmpty";
import StatusPill from "./components/StatusPill";
import { FALLBACK_SCENARIOS } from "./data/fallbackScenarios";
import {
  CHANNEL_LABELS,
  INTENT_LABELS,
  PROPERTY_LABELS,
  TRANSACTION_LABELS,
  labelFor,
} from "./lib/crm-labels";
import { VI } from "./lib/vi";
import type {
  ChannelId,
  Lead,
  LeadEvent,
  StreamEvent,
  TrafficScenario,
  TrafficSummary,
  TrafficSummaryEvent,
  Activity,
  Deal,
} from "./types";
import { cn } from "./lib/utils";

// --- Kanban Stages ---
const KANBAN_STAGES = [
  {
    id: "new",
    label: "Mới",
    description: "Vừa vào từ inbox đa kênh",
    icon: Flag,
    color: "bg-blue-100 text-blue-700",
    activeBtn: "bg-blue-600 text-white shadow-sm ring-2 ring-blue-200",
  },
  {
    id: "contacted",
    label: "Đã liên hệ",
    description: "CS đã gọi / nhắn xác nhận",
    icon: Phone,
    color: "bg-yellow-100 text-yellow-800",
    activeBtn: "bg-yellow-600 text-white shadow-sm ring-2 ring-yellow-200",
  },
  {
    id: "viewing",
    label: "Đặt xem",
    description: "Có lịch hẹn xem nhà",
    icon: Calendar,
    color: "bg-purple-100 text-purple-700",
    activeBtn: "bg-purple-600 text-white shadow-sm ring-2 ring-purple-200",
  },
  {
    id: "negotiating",
    label: "Thương lượng",
    description: "Đang đàm phán giá / pháp lý",
    icon: TrendingUp,
    color: "bg-orange-100 text-orange-800",
    activeBtn: "bg-orange-600 text-white shadow-sm ring-2 ring-orange-200",
  },
  {
    id: "won",
    label: "Đã chốt",
    description: "Ký HĐ / cọc thành công",
    icon: Building2,
    color: "bg-green-100 text-green-800",
    activeBtn: "bg-green-600 text-white shadow-sm ring-2 ring-green-200",
  },
  {
    id: "lost",
    label: "Đã mất",
    description: "Khách không tiếp tục",
    icon: User,
    color: "bg-red-100 text-red-700",
    activeBtn: "bg-red-600 text-white shadow-sm ring-2 ring-red-200",
  },
] as const;

// --- Channel Icons & Colors ---
const channelIcons: Record<string, string> = {
  facebook: "F",
  tiktok: "T",
  zalo: "Z",
  instagram: "I",
  shopee: "S",
  generic: "?",
};

const channelColors: Record<string, string> = {
  facebook: "bg-blue-600",
  tiktok: "bg-black",
  zalo: "bg-blue-500",
  instagram: "bg-gradient-to-br from-purple-500 to-pink-500",
  shopee: "bg-orange-500",
  generic: "bg-slate-500",
};

// --- AI Agents (khớp backend agents.py / GEMINI_API_KEY_1..6) ---
const AI_AGENTS = [
  { id: 1, name: "Agent Traffic", role: "Tổng hợp burst", color: "bg-blue-500", desc: "Sau mỗi kịch bản đổ traffic — summary & hot leads" },
  { id: 2, name: "Agent CRM Extract", role: "Phân loại lead", color: "bg-violet-500", desc: "Trích xuất BĐS + auto-reply FAQ" },
  { id: 3, name: "Agent Trưởng phòng", role: "Brief vận hành", color: "bg-orange-500", desc: "Brief cho manager / Odoo" },
  { id: 4, name: "Agent Telegram Reply", role: "Trả lời Telegram", color: "bg-cyan-500", desc: "Phản hồi khách qua bot" },
  { id: 5, name: "Agent Telegram Analyze", role: "Hội thoại → CRM", color: "bg-emerald-500", desc: "Phân tích chat → lead" },
  { id: 6, name: "Agent Compliance", role: "Kiểm soát pháp lý", color: "bg-red-500", desc: "Chặn cam kết ROI / pháp lý" },
];

function eventToLead(ev: LeadEvent): Lead {
  return {
    message_id: ev.message_id,
    channel: ev.channel,
    raw_text: ev.raw_text,
    customer_name: ev.customer_name,
    phone: ev.phone,
    product_interest: ev.product_interest,
    property_type: ev.property_type as any,
    location: ev.location,
    transaction_type: ev.transaction_type as any,
    budget_range: ev.budget_range,
    bedroom_count: ev.bedroom_count,
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
    pipeline_stage: "done",
    kanban_stage: "new",
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

// --- Sortable Lead Card ---
function SortableLeadCard({ lead, selectedId, onSelect }: { lead: Lead; selectedId: string | null; onSelect: (id: string) => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: lead.message_id });
  const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.3 : 1, zIndex: isDragging ? 999 : "auto" };
  const isSelected = selectedId === lead.message_id;
  return (
    <div ref={setNodeRef} style={style} {...attributes} onClick={() => onSelect(lead.message_id)} className={cn(
      "kanban-card p-5 rounded-2xl border bg-white shadow-sm cursor-pointer transition-all group relative",
      isSelected ? "border-purple-400 shadow-md ring-2 ring-purple-100" : "border-slate-200 hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300"
    )}>
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <div {...listeners} className="cursor-grab active:cursor-grabbing p-1.5 hover:bg-slate-100 rounded-lg">
          <GripVertical className="w-4.5 h-4.5 text-slate-400" />
        </div>
      </div>
      <div className="flex items-start gap-3 mb-4">
        <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center text-white text-base font-bold shadow-sm", channelColors[lead.channel as keyof typeof channelColors] || "bg-slate-500")}>
          {channelIcons[lead.channel as keyof typeof channelIcons] || "?"}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-slate-900 truncate">{lead.customer_name || "Khách ẩn danh"}</div>
          <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-1">
            {lead.property_type && <span>{lead.property_type}</span>}
            {lead.property_type && lead.location && <span>·</span>}
            {lead.location && <span>{lead.location}</span>}
          </div>
        </div>
      </div>
      <div className="text-sm text-slate-600 line-clamp-2 mb-4 leading-relaxed">{lead.summary || lead.raw_text}</div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {lead.urgency === "high" && (
            <span className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-red-100 text-red-700 font-semibold">
              <Flag className="w-3.5 h-3.5" /> HOT
            </span>
          )}
          {lead.tags && lead.tags.slice(0, 1).map((tag, i) => (
            <span key={i} className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Kanban Column ---
function KanbanColumn({
  stage,
  leads,
  selectedId,
  onSelect,
}: {
  stage: (typeof KANBAN_STAGES)[number];
  leads: Lead[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex flex-col w-88 flex-shrink-0">
      <div className="px-5 py-4 rounded-t-2xl border-b border-slate-200 bg-gradient-to-r from-slate-50 to-white sticky top-0 z-10 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-50">
              <stage.icon className="w-5 h-5 text-slate-600" />
            </div>
            <div>
              <div className="font-semibold text-base text-slate-900">{stage.label}</div>
              <div className="text-xs text-slate-500">{stage.description}</div>
            </div>
          </div>
          <span className="text-xs font-bold px-3.5 py-1.5 rounded-full bg-slate-200 text-slate-700">{leads.length}</span>
        </div>
      </div>
      <div className="flex-1 bg-slate-50/80 border-x border-b border-slate-200 rounded-b-2xl p-4 overflow-y-auto max-h-[calc(100vh-280px)]">
        <SortableContext items={leads.map((l) => l.message_id)} strategy={rectSortingStrategy}>
          <div className="space-y-4">
            {leads.map((lead) => (
              <SortableLeadCard key={lead.message_id} lead={lead} selectedId={selectedId} onSelect={onSelect} />
            ))}
          </div>
        </SortableContext>
        {leads.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-slate-400">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
              <stage.icon className="w-8 h-8 opacity-40" />
            </div>
            <div className="text-sm font-medium">Chưa có lead</div>
            <div className="text-xs text-slate-400 mt-1">Kéo thả lead vào đây</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const qc = useQueryClient();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState(false);
  const [status, setStatus] = useState<string>(VI.status.connecting);
  const [activeScenario, setActiveScenario] = useState<TrafficScenario | null>(null);
  const [aiFocus, setAiFocus] = useState<string | undefined>();
  const pendingRef = useRef<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<"traffic" | "crm">("traffic");
  const [activeLeadTab, setActiveLeadTab] = useState<"info" | "activities" | "deals">("info");
  const [activityBusy, setActivityBusy] = useState(false);
  const [dealBusy, setDealBusy] = useState(false);
  const [summaryWaitUntil, setSummaryWaitUntil] = useState(0);
  const [activeId, setActiveId] = useState<string | null>(null);

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

  const { data: initialLeads } = useQuery({
    queryKey: ["leads"],
    queryFn: () => fetchLeads(50),
    retry: 1,
    retryDelay: 8000,
  });
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

  const {
    data: trafficSummary,
    isFetching: trafficSummaryLoading,
  } = useQuery({
    queryKey: ["trafficSummary", activeScenario?.id],
    queryFn: () => fetchTrafficSummary(activeScenario!.id),
    enabled: !!activeScenario?.id,
    retry: false,
    refetchInterval: (query) => {
      if (!activeScenario?.id) return false;
      if (query.state.data) return false;
      if (summaryWaitUntil > 0 && Date.now() > summaryWaitUntil) return false;
      return 8000;
    },
  });
  const { data: selectedLead, isFetching: detailLoading } = useQuery({
    queryKey: ["lead", selectedId],
    queryFn: () => fetchLead(selectedId!),
    enabled: !!selectedId,
  });

  // --- Activities & Deals Queries ---
  const { data: leadActivities, refetch: refetchActivities } = useQuery({
    queryKey: ["activities", selectedId],
    queryFn: () => (selectedId ? fetchActivities(selectedId) : Promise.resolve([])),
    enabled: !!selectedId,
  });

  const { data: leadDeals, refetch: refetchDeals } = useQuery({
    queryKey: ["deals", selectedId],
    queryFn: () => (selectedId ? fetchDeals(selectedId) : Promise.resolve([])),
    enabled: !!selectedId,
  });

  useEffect(() => {
    if (!Array.isArray(initialLeads)) return;
    // Chỉ seed lần đầu — tránh ghi đè lead đang cập nhật qua SSE/poll khi query refetch
    setLeads((prev) => {
      if (prev.length > 0) return prev;
      return initialLeads.map((l) => ({
        ...l,
        kanban_stage: l.kanban_stage || "new",
        pipeline_stage: "done" as const,
      }));
    });
  }, [initialLeads]);

  const mergeLead = useCallback((incoming: Lead) => {
    if (!incoming || !incoming.message_id) return;
    setLeads((prev) => {
      if (!Array.isArray(prev)) return [];
      const idx = prev.findIndex((p) => p && p.message_id === incoming.message_id);
      if (idx < 0) return [{ ...incoming, kanban_stage: "new", pipeline_stage: "done" }, ...prev].slice(0, 80);
      const existing = prev[idx];
      const merged: Lead = {
        ...existing,
        ...incoming,
        kanban_stage: incoming.kanban_stage || existing.kanban_stage || "new",
        pipeline_stage: "done",
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
      };
      const rest = prev.filter((_, i) => i !== idx);
      return [merged, ...rest];
    });
  }, []);

  const handleStreamEvent = useCallback(
    (ev: StreamEvent) => {
      if (ev.type === "traffic_summary") {
        const summary = ev as TrafficSummaryEvent;
        qc.setQueryData<TrafficSummary | null>(
          ["trafficSummary", summary.scenario_id],
          {
            scenario_id: summary.scenario_id,
            title_vi: summary.title_vi,
            summary_vi: summary.summary_vi,
            hot_leads: summary.hot_leads,
            channels: summary.channels,
            recommendations: summary.recommendations,
            lead_count: summary.lead_count,
          }
        );
        setSummaryWaitUntil(0);
        return;
      }

      const leadEv = ev as LeadEvent;
      if (!leadEv || !leadEv.message_id) return;
      setLive(true);
      setStatus(statusFromEvent(leadEv));
      mergeLead(eventToLead(leadEv));

      if (leadEv.type === "lead_queued" || leadEv.type === "lead_processing") {
        pendingRef.current.add(leadEv.message_id);
      }
      if (leadEv.type === "lead_processed") {
        pendingRef.current.delete(leadEv.message_id);
        qc.invalidateQueries({ queryKey: ["metrics"] });
        qc.invalidateQueries({ queryKey: ["alerts"] });
      }
      if (leadEv.type === "auto_reply_sent") {
        qc.invalidateQueries({ queryKey: ["metrics"] });
      }
      if (selectedId === leadEv.message_id) {
        qc.invalidateQueries({ queryKey: ["lead", leadEv.message_id] });
      }
    },
    [mergeLead, qc, selectedId]
  );

  useEffect(() => {
    const close = connectLeadStream(handleStreamEvent);
    let timer: ReturnType<typeof setTimeout>;

    let pollIntervalMs = 8000;

    const poll = () => {
      fetchLeads(50)
        .then((rows) => {
          if (!Array.isArray(rows)) return;
          pollIntervalMs = pendingRef.current.size > 0 ? 2000 : 8000;
          setLeads((prev) => {
            if (!Array.isArray(prev)) prev = [];
            const byId = new Map(
              prev.filter((l) => l && l.message_id).map((l) => [l.message_id, l])
            );
            for (const row of rows) {
              if (!row || !row.message_id) continue;
              const existing = byId.get(row.message_id);
              byId.set(row.message_id, {
                ...existing,
                ...row,
                kanban_stage: row.kanban_stage || existing?.kanban_stage || "new",
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
        .catch(() => {
          pollIntervalMs = 15000;
          setStatus(VI.status.pollFallback);
        })
        .finally(() => {
          timer = setTimeout(poll, pollIntervalMs);
        });
    };

    poll();
    return () => {
      close();
      clearTimeout(timer);
    };
  }, [handleStreamEvent]);

  const activeChannels = [
    ...new Set(
      leads
        .filter((l) => l && l.channel)
        .map((l) => l.channel as ChannelId)
    ),
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
      setSummaryWaitUntil(Date.now() + 90_000);
      qc.removeQueries({ queryKey: ["trafficSummary", scenario.id] });
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    } catch (e) {
      setStatus(`Lỗi: ${e instanceof Error ? e.message : "đổ traffic thất bại"}`);
    } finally {
      setBusy(false);
    }
  };

  // --- Drag & Drop ---
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragStart = (event: any) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = async (event: any) => {
    const { active, over } = event;
    setActiveId(null);
    if (!over) return;

    const activeLead = leads.find((l) => l.message_id === active.id);
    if (!activeLead) return;

    const activeLeadStage = activeLead.kanban_stage;
    let targetStage = KANBAN_STAGES.find((s) => s.id === over.id)?.id;

    if (!targetStage) {
      const overLead = leads.find((l) => l.message_id === over.id);
      if (overLead) {
        targetStage = overLead.kanban_stage;
      }
    }

    if (!targetStage || targetStage === activeLeadStage) return;

    try {
      await updateLeadStage(active.id, targetStage);
      setLeads((prev) =>
        prev.map((l) =>
          l.message_id === active.id ? { ...l, kanban_stage: targetStage } : l
        )
      );
      qc.invalidateQueries({ queryKey: ["lead", active.id] });
    } catch (e) {
      console.error(e);
    }
  };

  const detail =
    selectedLead ||
    (selectedId ? leads.find((l) => l.message_id === selectedId) ?? null : null);

  const hasPending = leads.some(
    (l) => l.pipeline_stage === "queued" || l.pipeline_stage === "processing"
  );

  return (
    <div className="app-shell min-h-screen text-slate-900 font-sans">
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 shadow-sm backdrop-blur-md">
        <div className="px-6 py-3.5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="flex items-center gap-2 text-xl font-bold tracking-tight text-slate-900">
                <Building2 className="h-6 w-6 text-purple-600" />
                {VI.appTitle}
              </h1>
              <p className="mt-0.5 text-sm text-slate-500">{VI.appSubtitle}</p>
            </div>
            <StatusPill
              live={live}
              busy={busy}
              hasPending={hasPending}
              status={status}
              leadCount={leads.length}
            />
          </div>

          <div className="mt-4 flex gap-1 border-b border-slate-200">
            <button
              type="button"
              onClick={() => setActiveTab("traffic")}
              className={cn(
                "px-5 py-3 text-sm font-semibold rounded-t-xl transition-all",
                activeTab === "traffic"
                  ? "bg-purple-600 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <div className="flex items-center gap-2">
                <LayoutDashboard className="h-4 w-4" />
                {VI.tabs.traffic}
              </div>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("crm")}
              className={cn(
                "px-5 py-3 text-sm font-semibold rounded-t-xl transition-all",
                activeTab === "crm"
                  ? "bg-purple-600 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <div className="flex items-center gap-2">
                <KanbanSquare className="h-4 w-4" />
                {VI.tabs.crm}
              </div>
            </button>
          </div>

          {activeTab === "traffic" && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
              {AI_AGENTS.map((agent) => (
                <div key={agent.id} className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={cn(agent.color, "p-1.5 rounded-lg")}>
                      <User className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold truncate">{agent.name}</div>
                      <div className="text-[10px] text-slate-500">{agent.role}</div>
                    </div>
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  </div>
                  <div className="text-[9px] text-slate-400 line-clamp-2">{agent.desc}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </header>

      <main className="p-5 lg:p-6">
        {activeTab === "traffic" && (
          <div className="space-y-5">
            <DemoWorkflowBanner />
            <div className="space-y-4">
              <MetricsBar metrics={metrics} />
              <MultiChannelHub metrics={metrics} activeChannels={activeChannels} />
            </div>
            <TrafficSummaryCard
              summary={trafficSummary ?? null}
              loading={trafficSummaryLoading && !!activeScenario}
            />
            <div className="grid gap-5 xl:grid-cols-[280px_1fr_280px]">
            <aside className="space-y-4">
              <TrafficScenarios
                scenarios={scenarios}
                activeId={activeScenario?.id ?? null}
                busy={busy}
                apiError={scenariosApiError}
                onBurst={onBurst}
              />
              <ChannelButtons onSend={onSendChannel} busy={busy} />
              <RoiCalculator />
            </aside>

            <section className="flex flex-col gap-4">
              <LeadStream leads={leads} selectedId={selectedId} onSelect={setSelectedId} />
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-white border border-slate-200 shadow-lg rounded-2xl overflow-hidden">
                  <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-6 py-5">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                      <User className="h-4 w-4 text-purple-600" />
                      {VI.detail.title}
                    </div>
                  </div>
                  {detailLoading && selectedId && !detail ? (
                    <div className="flex items-center justify-center gap-2 px-6 py-16 text-sm text-slate-500">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-purple-600 border-t-transparent" />
                      Đang tải hồ sơ…
                    </div>
                  ) : detail ? (
                    <div className="p-6 space-y-5">
                      <div className="text-center pb-5 border-b border-slate-100">
                        <div className="w-24 h-24 mx-auto mb-4 border-4 border-white shadow-xl rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-3xl font-bold">
                          {detail.customer_name?.charAt(0) || "?"}
                        </div>
                        <div className="font-bold text-2xl text-slate-900">{detail.customer_name || "Khách ẩn danh"}</div>
                        {detail.company && <div className="text-slate-600 mt-2 flex items-center justify-center gap-1.5"><Building2 className="w-4 h-4" /> {detail.company}</div>}
                        {detail.phone && <div className="font-mono text-purple-600 mt-3 text-base flex items-center justify-center gap-1.5"><Phone className="w-4 h-4" /> {detail.phone}</div>}
                        {detail.email && <div className="text-slate-600 mt-1 text-sm flex items-center justify-center gap-1.5"><Mail className="w-4 h-4" /> {detail.email}</div>}
                      </div>
                      <div className="space-y-4">
                        <div>
                          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                            <ActivityIcon className="w-3.5 h-3.5" />
                            Nhu cầu khách hàng
                          </div>
                          <div className="text-sm text-slate-700 bg-slate-50 p-5 rounded-xl border border-slate-100">{detail.summary || detail.raw_text}</div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
                            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5 flex items-center gap-1.5"><Globe className="w-3.5 h-3.5" />Kênh tiếp cận</div>
                            <div className="font-medium text-slate-700">{CHANNEL_LABELS[detail.channel] || detail.channel}</div>
                          </div>
                          <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
                            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Ý định chính</div>
                            <div className="font-medium text-slate-700">{labelFor(INTENT_LABELS, detail.intent as string)}</div>
                          </div>
                          {detail.property_type && (
                            <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
                              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5 flex items-center gap-1.5"><Building2 className="w-3.5 h-3.5" />Loại BĐS quan tâm</div>
                              <div className="font-medium text-slate-700">{labelFor(PROPERTY_LABELS, detail.property_type)}</div>
                            </div>
                          )}
                          {detail.location && (
                            <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
                              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5 flex items-center gap-1.5"><MapIcon className="w-3.5 h-3.5" />Vị trí mong muốn</div>
                              <div className="font-medium text-slate-700">{detail.location}</div>
                            </div>
                          )}
                          {detail.budget_range && (
                            <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
                              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Ngân sách dự kiến</div>
                              <div className="font-medium text-purple-700">{detail.budget_range}</div>
                            </div>
                          )}
                          {detail.bedroom_count && (
                            <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
                              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Số phòng ngủ</div>
                              <div className="font-medium text-slate-700">{detail.bedroom_count}</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <LeadDetailEmpty />
                  )}
                </div>
                <AlertTicker alerts={alerts ?? []} />
              </div>
            </section>

            <aside className="hidden xl:block space-y-4">
              <AiCapabilities focus={aiFocus} />
            </aside>
            </div>
          </div>
        )}

        {activeTab === "crm" && (
          <div className="flex h-[calc(100vh-200px)] flex-col gap-3">
            <p className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 shadow-sm">
              {VI.crm.kanbanHint}
            </p>
            <div className="grid min-h-0 flex-1 gap-6 lg:grid-cols-[1fr_480px] xl:grid-cols-[1fr_520px]">
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
              <div className="h-full overflow-x-auto overflow-y-hidden">
                <div className="flex gap-5 p-1 min-w-max h-full">
                  {KANBAN_STAGES.map((stage) => {
                    const stageLeads = leads.filter((l) => l && l.kanban_stage === stage.id);
                    return <KanbanColumn key={stage.id} stage={stage} leads={stageLeads} selectedId={selectedId} onSelect={setSelectedId} />;
                  })}
                </div>
              </div>
              <DragOverlay>
                {activeId ? (
                  <div className="opacity-95 shadow-2xl rounded-2xl border-2 border-purple-500 bg-white p-6 transform scale-105">
                    {(() => {
                      const lead = leads.find((l) => l && l.message_id === activeId);
                      return lead ? (
                        <div>
                          <div className="font-bold text-base text-slate-900">{lead.customer_name || "Khách ẩn danh"}</div>
                          <div className="text-sm text-slate-500 mt-2">{lead.summary || lead.raw_text}</div>
                          <div className="flex items-center gap-2 mt-3">
                            <span className={cn("text-xs px-2 py-1 rounded-full font-semibold", channelColors[lead.channel as keyof typeof channelColors] || "bg-slate-500", "text-white")}>{lead.channel}</span>
                          </div>
                        </div>
                      ) : null;
                    })()}
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>

            <div className="h-full space-y-4 overflow-y-auto">
              {!detail ? (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 shadow-sm">
                  <LeadDetailEmpty compact />
                  <p className="mt-4 text-center text-xs text-slate-500">{VI.crm.noLeadSelected}</p>
                </div>
              ) : (
                <div className="bg-white border border-slate-200 shadow-lg rounded-2xl overflow-hidden sticky top-0">
                  <div className="flex border-b border-slate-200 bg-slate-50">
                    <button onClick={() => setActiveLeadTab("info")} className={cn("flex-1 px-5 py-3.5 text-sm font-semibold transition-all", activeLeadTab === "info" ? "bg-white text-purple-600 border-b-2 border-purple-600" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100")}>
                      <div className="flex items-center justify-center gap-1.5"><User className="w-4.5 h-4.5" /> Thông tin</div>
                    </button>
                    <button onClick={() => setActiveLeadTab("activities")} className={cn("flex-1 px-5 py-3.5 text-sm font-semibold transition-all", activeLeadTab === "activities" ? "bg-white text-purple-600 border-b-2 border-purple-600" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100")}>
                      <div className="flex items-center justify-center gap-1.5"><ActivityIcon className="w-4.5 h-4.5" /> Hoạt động</div>
                    </button>
                    <button onClick={() => setActiveLeadTab("deals")} className={cn("flex-1 px-5 py-3.5 text-sm font-semibold transition-all", activeLeadTab === "deals" ? "bg-white text-purple-600 border-b-2 border-purple-600" : "text-slate-500 hover:text-slate-700 hover:bg-slate-100")}>
                      <div className="flex items-center justify-center gap-1.5"><Briefcase className="w-4.5 h-4.5" /> Cơ hội</div>
                    </button>
                  </div>

                  <div className="p-5 space-y-5">
                    {activeLeadTab === "info" && (
                      <div className="space-y-5">
                        <div className="text-center pb-4 border-b border-slate-100">
                          <div className="w-24 h-24 mx-auto mb-4 border-4 border-white shadow-lg rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-3xl font-bold">
                            {detail.customer_name?.charAt(0) || "?"}
                          </div>
                          <div className="font-bold text-2xl text-slate-900">{detail.customer_name || "Khách ẩn danh"}</div>
                          {detail.company && <div className="text-slate-600 mt-1 flex items-center justify-center gap-1.5"><Building2 className="w-4 h-4" /> {detail.company}</div>}
                          {detail.phone && <div className="font-mono text-purple-600 mt-2 text-base flex items-center justify-center gap-1.5"><Phone className="w-4 h-4" /> {detail.phone}</div>}
                          {detail.email && <div className="text-slate-600 mt-1 text-sm flex items-center justify-center gap-1.5"><Mail className="w-4 h-4" /> {detail.email}</div>}
                        </div>

                        <div className="space-y-4">
                          <div>
                            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                              <Tag className="w-3.5 h-3.5" />
                              {VI.crm.pipelineStatus}
                            </div>
                            <div className="flex items-center gap-3 flex-wrap">
                              {KANBAN_STAGES.map((stage, idx) => (
                                <div key={stage.id} className="flex items-center gap-2">
                                  <button onClick={async () => {
                                    try {
                                      await updateLeadStage(detail.message_id, stage.id);
                                      setLeads((prev) => prev.map((l) => l.message_id === detail.message_id ? { ...l, kanban_stage: stage.id } : l));
                                      qc.invalidateQueries({ queryKey: ["lead", detail.message_id] });
                                    } catch (e) { console.error(e); }
                                  }} className={cn(
                                    "rounded-lg px-3 py-2 text-xs font-semibold transition-all",
                                    detail.kanban_stage === stage.id
                                      ? stage.activeBtn
                                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                                  )}>
                                    {stage.label}
                                  </button>
                                  {idx < KANBAN_STAGES.length - 1 && <span className="text-slate-300">→</span>}
                                </div>
                              ))}
                            </div>
                          </div>

                          <div>
                            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Nhu cầu</div>
                            <div className="text-sm text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-100">{detail.summary || detail.raw_text}</div>
                          </div>

                          <div className="grid grid-cols-2 gap-3">
                            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1 flex items-center gap-1.5"><Globe className="w-3.5 h-3.5" />Kênh</div>
                              <div className="font-medium text-slate-700">{CHANNEL_LABELS[detail.channel] || detail.channel}</div>
                            </div>
                            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Ý định</div>
                              <div className="font-medium text-slate-700">{labelFor(INTENT_LABELS, detail.intent as string)}</div>
                            </div>
                            {detail.property_type && (
                              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1 flex items-center gap-1.5"><Building2 className="w-3.5 h-3.5" />Loại BĐS</div>
                                <div className="font-medium text-slate-700">{labelFor(PROPERTY_LABELS, detail.property_type)}</div>
                              </div>
                            )}
                            {detail.location && (
                              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1 flex items-center gap-1.5"><MapIcon className="w-3.5 h-3.5" />Vị trí</div>
                                <div className="font-medium text-slate-700">{detail.location}</div>
                              </div>
                            )}
                            {detail.transaction_type && detail.transaction_type !== "other" && (
                              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Mục đích</div>
                                <div className="font-medium text-slate-700">{labelFor(TRANSACTION_LABELS, detail.transaction_type)}</div>
                              </div>
                            )}
                            {detail.budget_range && (
                              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Ngân sách</div>
                                <div className="font-medium text-purple-700">{detail.budget_range}</div>
                              </div>
                            )}
                            {detail.bedroom_count && (
                              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Phòng ngủ</div>
                                <div className="font-medium text-slate-700">{detail.bedroom_count}</div>
                              </div>
                            )}
                          </div>
                        </div>

                        <div>
                          <div className="border-slate-200 my-4 border-t" />
                          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                            <Bot className="w-4 h-4 text-purple-600" />
                            Đề xuất từ Trưởng phòng AI
                          </div>
                          <div className="text-sm text-slate-700 bg-gradient-to-br from-purple-50 to-blue-50 p-5 rounded-xl border border-purple-200">
                            {detail.ai_manager_note ? (
                              <div className="whitespace-pre-line">{detail.ai_manager_note}</div>
                            ) : (
                              <div className="space-y-3">
                                <div className="flex items-start gap-2"><Phone className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" /><p><strong>Liên hệ:</strong> Gọi điện trong 30 phút tới</p></div>
                                <div className="flex items-start gap-2"><Calendar className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" /><p><strong>Lịch hẹn:</strong> Đặt lịch xem nhà vào cuối tuần</p></div>
                                <div className="flex items-start gap-2"><Building2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" /><p><strong>Dự án:</strong> Giới thiệu {detail.property_type || "căn hộ"} tại {detail.location || "Quận 1"}</p></div>
                                <div className="flex items-start gap-2"><TrendingUp className="w-4 h-4 text-orange-600 mt-0.5 flex-shrink-0" /><p><strong>Ưu tiên:</strong> {detail.urgency === "high" ? "Cao - Khách có nhu cầu gấp" : "Trung bình"}</p></div>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {activeLeadTab === "activities" && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between mb-4">
                          <div className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                            <ActivityIcon className="w-4 h-4" />
                            Lịch sử hoạt động
                          </div>
                          <button
                            disabled={activityBusy}
                            onClick={async () => {
                              if (!selectedId) return;
                              setActivityBusy(true);
                              try {
                                await createActivity(selectedId, { type: "call", title: "Gọi điện tư vấn BĐS", created_by: "CS Team" });
                                refetchActivities();
                              } catch (e) { console.error(e); } finally { setActivityBusy(false); }
                            }}
                            className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5"
                          >
                            <Plus className="w-3.5 h-3.5" /> + Gọi điện
                          </button>
                        </div>
                        <div className="space-y-3">
                          {leadActivities && leadActivities.length > 0 ? leadActivities.map((act) => (
                            <div key={act.id} className="flex gap-3 p-4 bg-slate-50 rounded-xl border border-slate-100">
                              <div className="w-9 h-9 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
                                {act.type === "call" ? <Phone className="w-4 h-4" /> : act.type === "meeting" ? <Calendar className="w-4 h-4" /> : <ActivityIcon className="w-4 h-4" />}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2">
                                  <div className="font-semibold text-sm text-slate-900 truncate">{act.title}</div>
                                  <div className="text-xs text-slate-400 shrink-0">{act.created_at ? new Date(act.created_at).toLocaleDateString("vi-VN") : ""}</div>
                                </div>
                                {act.content && <div className="text-sm text-slate-600 mt-1">{act.content}</div>}
                                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold mt-2 inline-block ${act.completed ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}`}>
                                  {act.completed ? "Hoàn thành" : "Chờ xử lý"}
                                </span>
                              </div>
                            </div>
                          )) : (
                            <div className="text-center py-8 text-slate-400">
                              <ActivityIcon className="w-8 h-8 mx-auto mb-2 opacity-30" />
                              <div className="text-sm">Chưa có hoạt động nào</div>
                              <div className="text-xs mt-1">Nhấn nút để ghi lại cuộc gọi đầu tiên</div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {activeLeadTab === "deals" && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between mb-4">
                          <div className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                            <Briefcase className="w-4 h-4" />
                            Cơ hội kinh doanh
                          </div>
                          <button
                            disabled={dealBusy}
                            onClick={async () => {
                              if (!selectedId || !detail) return;
                              setDealBusy(true);
                              const pLabel = labelFor(PROPERTY_LABELS, detail.property_type) === "—" ? "BĐS" : labelFor(PROPERTY_LABELS, detail.property_type);
                              try {
                                await createDeal(selectedId, { name: `${pLabel} - ${detail.location || "Việt Nam"}`, currency: "VND", probability: 30, description: detail.summary || "" });
                                refetchDeals();
                              } catch (e) { console.error(e); } finally { setDealBusy(false); }
                            }}
                            className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5"
                          >
                            <Plus className="w-3.5 h-3.5" /> Tạo cơ hội
                          </button>
                        </div>
                        <div className="space-y-3">
                          {leadDeals && leadDeals.length > 0 ? leadDeals.map((deal) => {
                            const prob = Math.min(100, Math.max(0, deal.probability));
                            const probColor = prob >= 70 ? "bg-green-500" : prob >= 40 ? "bg-yellow-500" : "bg-slate-400";
                            return (
                              <div key={deal.id} className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
                                <div className="flex items-start justify-between mb-3">
                                  <div>
                                    <div className="font-semibold text-slate-900">{deal.name}</div>
                                    {deal.description && <div className="text-xs text-slate-500 mt-1">{deal.description}</div>}
                                  </div>
                                  {deal.amount && <div className="text-base font-bold text-blue-600 shrink-0 ml-2">{new Intl.NumberFormat("vi-VN").format(deal.amount)} {deal.currency}</div>}
                                </div>
                                <div className="space-y-1.5">
                                  <div className="flex items-center justify-between text-xs text-slate-500">
                                    <span>Xác suất</span><span className="font-semibold">{prob}%</span>
                                  </div>
                                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden"><div className={`h-full rounded-full ${probColor}`} style={{ width: `${prob}%` }} /></div>
                                </div>
                                {deal.close_date && <div className="flex items-center gap-1.5 mt-3 text-xs text-slate-500"><Calendar className="w-3.5 h-3.5" />Dự kiến đóng: {new Date(deal.close_date).toLocaleDateString("vi-VN")}</div>}
                              </div>
                            );
                          }) : (
                            <div className="text-center py-8 text-slate-400">
                              <Briefcase className="w-8 h-8 mx-auto mb-2 opacity-30" />
                              <div className="text-sm">Chưa có cơ hội nào</div>
                              <div className="text-xs mt-1">Tạo cơ hội khi khách tiến vào đàm phán</div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
