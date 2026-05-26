export type Lead = {
  message_id: string;
  channel: string;
  raw_text?: string;
  customer_name?: string;
  phone?: string;
  product_interest?: string;
  language?: string;
  order_id?: string;
  shop_id?: string;
  locale?: string;
  urgency: string;
  sentiment: string;
  intent: string;
  summary?: string;
  alert_sent?: boolean;
  alert_type?: string;
  auto_reply_sent?: boolean;
  auto_reply_content?: string;
  processed_at?: string;
  pipeline_stage?: "queued" | "processing" | "done";
};

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
  language?: string;
  order_id?: string;
  shop_id?: string;
  locale?: string;
  auto_reply_content?: string;
  processed_at?: string;
  queue_depth?: number;
};

export type MetricsSummary = {
  processed_1h: number;
  processed_24h: number;
  alerts_24h: number;
  auto_replies_24h: number;
  hot_leads_1h: number;
  by_channel_24h: Record<string, number>;
  as_of: string;
};

export type ChannelId = "facebook" | "tiktok" | "shopee" | "generic";

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
