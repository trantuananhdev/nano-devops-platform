// ─── Core BĐS Domain Types ─────────────────────────────────────────────────

export type KanbanStage = "new" | "contacted" | "viewing" | "negotiating" | "won" | "lost";

export type ChannelId = "facebook" | "tiktok" | "zalo" | "instagram" | "shopee" | "generic";

/** Ý định của khách hàng BĐS — nhất quán với backend llm_gemini.py */
export type LeadIntent =
  | "purchase"
  | "inquiry"
  | "schedule_viewing"
  | "price_inquiry"
  | "legal_inquiry"
  | "complaint"
  | "other";

export type TransactionType = "buy" | "rent" | "invest" | "other";

export type PropertyType = "apartment" | "house" | "land" | "commercial" | "other";

// ─── Chat & Activity ────────────────────────────────────────────────────────

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type ActivityType = "call" | "meeting" | "note" | "email" | "task" | "sms";

export type Activity = {
  id: string;
  type: ActivityType;
  title: string;
  content?: string;
  created_at: string;
  due_date?: string;
  completed: boolean;
  created_by: string;
};

// ─── Deal / Opportunity ─────────────────────────────────────────────────────

export type Deal = {
  id: string;
  lead_id: string;
  name: string;
  amount?: number;
  currency: string;
  probability: number;
  close_date?: string;
  description?: string;
};

// ─── Note ───────────────────────────────────────────────────────────────────

export type Note = {
  id: string;
  content: string;
  created_by: string;
  created_at: string;
};

// ─── Lead (core CRM entity) ─────────────────────────────────────────────────

export type Lead = {
  message_id: string;
  channel: string;
  raw_text?: string;
  customer_name?: string;
  phone?: string;
  email?: string;
  product_interest?: string;

  // BĐS-specific fields (nhất quán với backend llm_gemini.py)
  property_type?: PropertyType;
  location?: string;
  transaction_type?: TransactionType;
  budget_range?: string;
  bedroom_count?: string;

  // AI analysis
  urgency: string;
  sentiment: string;
  intent: LeadIntent | string;
  language?: string;
  summary?: string;
  alert_sent?: boolean;
  alert_type?: string;
  auto_reply_sent?: boolean;
  auto_reply_content?: string;
  processed_at?: string;

  // Pipeline tracking
  pipeline_stage?: "queued" | "processing" | "done";
  kanban_stage?: KanbanStage;

  // AI outputs
  chat_history?: ChatMessage[];
  ai_manager_note?: string;

  // CRM enrichment
  tags?: string[];
  assigned_to?: string;
  source?: string;
  company?: string;
  website?: string;
  address?: string;
  city?: string;
  country?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
  last_contacted_at?: string;

  // Related entities
  activities?: Activity[];
  deals?: Deal[];
  notes?: Note[] | string[];
};

// ─── SSE Stream Event ────────────────────────────────────────────────────────

export type LeadEvent = {
  type: string;
  message_id: string;
  channel: string;
  urgency: string;
  sentiment: string;
  intent: string;
  alert_sent: boolean;
  auto_reply_sent: boolean;
  summary?: string;
  raw_text?: string;
  customer_name?: string;
  phone?: string;
  product_interest?: string;
  property_type?: string;
  location?: string;
  transaction_type?: string;
  budget_range?: string;
  bedroom_count?: string;
  language?: string;
  order_id?: string;
  shop_id?: string;
  locale?: string;
  auto_reply_content?: string;
  processed_at?: string;
  queue_depth?: number;
};

export type StreamEvent = LeadEvent | TrafficSummaryEvent;

export type TrafficSummaryEvent = {
  type: "traffic_summary";
  scenario_id: string;
  title_vi?: string;
  summary_vi?: string;
  hot_leads?: number;
  channels?: Record<string, number>;
  recommendations?: string[];
  lead_count?: number;
};

// ─── Metrics ─────────────────────────────────────────────────────────────────

export type MetricsSummary = {
  processed_1h: number;
  processed_24h: number;
  alerts_24h: number;
  auto_replies_24h: number;
  hot_leads_1h: number;
  by_channel_24h: Record<string, number>;
  as_of: string;
};

// ─── Traffic Scenarios ────────────────────────────────────────────────────────

export type TrafficScenario = {
  id: string;
  title_vi: string;
  description_vi: string;
  crm_stage_vi: string;
  ai_focus_vi: string;
  icon: string;
  channels?: ChannelId[];
  message_count: number;
  delay_ms: number;
};

export type TrafficSummary = {
  scenario_id: string;
  title_vi?: string;
  summary_vi?: string;
  hot_leads?: number;
  channels?: Record<string, number>;
  recommendations?: string[];
  lead_count?: number;
  created_at?: string;
};
