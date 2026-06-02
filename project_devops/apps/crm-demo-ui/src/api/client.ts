import type { Lead, StreamEvent, MetricsSummary, TrafficScenario, TrafficSummary, Activity, Deal } from "../types";

const API_BASE = import.meta.env.VITE_CRM_API_BASE || "";
const SSE_URL = import.meta.env.VITE_SSE_URL || `${API_BASE}/api/v1/events/stream`;
const DEMO_KEY = import.meta.env.VITE_DEMO_KEY || "";

function headers(): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" };
  if (DEMO_KEY) h["X-Demo-Key"] = DEMO_KEY;
  return h;
}

export type DemoSendResult = {
  status: string;
  job_id: string;
  message_id?: string;
  queued_at?: string;
  queue_depth?: number;
  duplicate?: boolean;
};

export async function fetchScenarios(): Promise<TrafficScenario[]> {
  const res = await fetch(`${API_BASE}/api/v1/demo/scenarios`, { headers: headers() });
  if (!res.ok) throw new Error("Không tải được kịch bản traffic");
  return res.json();
}

export type TrafficBurstResult = {
  status: string;
  scenario_id: string;
  title_vi?: string;
  accepted_count: number;
  message_ids: string[];
  total_planned: number;
};

export async function demoTrafficBurst(scenarioId: string): Promise<TrafficBurstResult> {
  const res = await fetch(`${API_BASE}/api/v1/demo/traffic-burst`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ scenario_id: scenarioId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function demoSend(
  channel: string,
  templateId?: string,
  category?: string
): Promise<DemoSendResult> {
  const res = await fetch(`${API_BASE}/api/v1/demo/send`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ channel, template_id: templateId, category }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function parseApiError(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (body?.detail?.message) return String(body.detail.message);
    if (body?.detail) return typeof body.detail === "string" ? body.detail : fallback;
  } catch {
    /* ignore */
  }
  return fallback;
}

export async function fetchLeads(limit = 50, kanbanStage?: string): Promise<Lead[]> {
  const qs = new URLSearchParams({ limit: limit.toString() });
  if (kanbanStage) qs.set("kanban_stage", kanbanStage);
  const res = await fetch(`${API_BASE}/api/v1/leads?${qs.toString()}`, { headers: headers() });
  if (!res.ok) {
    const msg = await parseApiError(res, "Không tải được danh sách lead");
    throw new Error(res.status === 503 ? `${msg} (chạy migration DB CRM)` : msg);
  }
  return res.json();
}

export async function fetchLead(id: string): Promise<Lead> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${id}`, { headers: headers() });
  if (!res.ok) throw new Error("Lead not found");
  return res.json();
}

export async function updateLead(messageId: string, updates: Partial<Lead>): Promise<Lead> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${messageId}`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("Failed to update lead");
  return res.json();
}

export async function fetchAlerts(): Promise<Lead[]> {
  const res = await fetch(`${API_BASE}/api/v1/alerts`, { headers: headers() });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchMetrics(): Promise<MetricsSummary> {
  const res = await fetch(`${API_BASE}/api/v1/metrics/summary`, { headers: headers() });
  if (!res.ok) throw new Error("Metrics unavailable");
  return res.json();
}

export async function fetchQueueDepth(): Promise<number> {
  const res = await fetch(`${API_BASE}/api/v1/queue/status`, { headers: headers() });
  if (!res.ok) return 0;
  const data = await res.json();
  return Number(data.depth ?? 0);
}

export async function fetchTrafficSummary(
  scenarioId: string
): Promise<TrafficSummary | null> {
  const qs = `?scenario_id=${encodeURIComponent(scenarioId)}`;
  const res = await fetch(`${API_BASE}/api/v1/traffic/summary${qs}`, { headers: headers() });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Không tải được traffic summary");
  return res.json();
}

export async function updateLeadStage(
  messageId: string, 
  kanbanStage: string,
  aiManagerNote?: string
): Promise<Lead> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${messageId}/stage`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify({ 
      kanban_stage: kanbanStage,
      ai_manager_note: aiManagerNote
    }),
  });
  if (!res.ok) throw new Error("Failed to update lead stage");
  return res.json();
}

// --- Activities API ---

export async function fetchActivities(leadId: string): Promise<Activity[]> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/activities`, { headers: headers() });
  if (!res.ok) return [];
  return res.json();
}

export async function createActivity(leadId: string, activity: Omit<Activity, "id" | "created_at" | "completed">): Promise<Activity> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/activities`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(activity),
  });
  if (!res.ok) throw new Error("Failed to create activity");
  return res.json();
}

export async function updateActivity(leadId: string, activityId: string, updates: Partial<Activity>): Promise<Activity> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/activities/${activityId}`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("Failed to update activity");
  return res.json();
}

export async function deleteActivity(leadId: string, activityId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/activities/${activityId}`, {
    method: "DELETE",
    headers: headers(),
  });
  if (!res.ok) throw new Error("Failed to delete activity");
}

// --- Deals API ---

export async function fetchDeals(leadId: string): Promise<Deal[]> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/deals`, { headers: headers() });
  if (!res.ok) return [];
  return res.json();
}

export async function createDeal(leadId: string, deal: Omit<Deal, "id" | "lead_id">): Promise<Deal> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/deals`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(deal),
  });
  if (!res.ok) throw new Error("Failed to create deal");
  return res.json();
}

export async function updateDeal(leadId: string, dealId: string, updates: Partial<Deal>): Promise<Deal> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/deals/${dealId}`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("Failed to update deal");
  return res.json();
}

export async function deleteDeal(leadId: string, dealId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/deals/${dealId}`, {
    method: "DELETE",
    headers: headers(),
  });
  if (!res.ok) throw new Error("Failed to delete deal");
}

// --- Notes API ---

export async function addNote(leadId: string, content: string, createdBy: string): Promise<Lead> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/notes`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ content, created_by: createdBy }),
  });
  if (!res.ok) throw new Error("Failed to add note");
  return res.json();
}

// --- Tags API ---

export async function updateTags(leadId: string, tags: string[]): Promise<Lead> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${leadId}/tags`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify({ tags }),
  });
  if (!res.ok) throw new Error("Failed to update tags");
  return res.json();
}

export function connectLeadStream(onEvent: (ev: StreamEvent) => void): () => void {
  let es: EventSource | null = null;
  let closed = false;
  let retryMs = 1000;

  const connect = () => {
    if (closed) return;
    es = new EventSource(SSE_URL);
    const onMessage = (e: MessageEvent) => {
      retryMs = 1000;
      try {
        const data = JSON.parse(e.data) as StreamEvent;
        onEvent(data);
      } catch {
        /* ignore parse errors */
      }
    };
    es.addEventListener("lead", onMessage);
    es.onerror = () => {
      es?.close();
      es = null;
      if (closed) return;
      window.setTimeout(connect, retryMs);
      retryMs = Math.min(retryMs * 2, 15_000);
    };
  };

  connect();
  return () => {
    closed = true;
    es?.close();
  };
}

export { API_BASE, SSE_URL };
