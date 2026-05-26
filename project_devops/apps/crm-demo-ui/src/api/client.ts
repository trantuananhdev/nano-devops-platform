import type { Lead, LeadEvent, MetricsSummary, TrafficScenario } from "../types";

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

export async function fetchLeads(limit = 50): Promise<Lead[]> {
  const res = await fetch(`${API_BASE}/api/v1/leads?limit=${limit}`, { headers: headers() });
  if (!res.ok) throw new Error("Failed to load leads");
  return res.json();
}

export async function fetchLead(id: string): Promise<Lead> {
  const res = await fetch(`${API_BASE}/api/v1/leads/${id}`, { headers: headers() });
  if (!res.ok) throw new Error("Lead not found");
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

export function connectLeadStream(onEvent: (ev: LeadEvent) => void): () => void {
  let es: EventSource | null = null;
  let closed = false;
  let retryMs = 1000;

  const connect = () => {
    if (closed) return;
    es = new EventSource(SSE_URL);
    es.addEventListener("lead", (e) => {
      retryMs = 1000;
      try {
        onEvent(JSON.parse((e as MessageEvent).data));
      } catch {
        /* ignore parse errors */
      }
    });
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
