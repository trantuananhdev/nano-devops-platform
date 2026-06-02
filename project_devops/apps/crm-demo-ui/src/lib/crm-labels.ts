/** Nhãn nghiệp vụ CRM BĐS — dùng chung UI */

export const CHANNEL_LABELS: Record<string, string> = {
  facebook: "Facebook",
  tiktok: "TikTok",
  zalo: "Zalo",
  instagram: "Instagram",
  shopee: "Shopee",
  generic: "Website / Inbox",
};

export const INTENT_LABELS: Record<string, string> = {
  purchase: "Mua BĐS",
  inquiry: "Tư vấn",
  schedule_viewing: "Đặt lịch xem",
  price_inquiry: "Hỏi giá",
  legal_inquiry: "Hỏi pháp lý",
  complaint: "Phàn nàn",
  other: "Khác",
};

export const PROPERTY_LABELS: Record<string, string> = {
  apartment: "Căn hộ",
  house: "Nhà / Biệt thự",
  land: "Đất nền",
  commercial: "Shophouse",
  other: "Khác",
};

export const TRANSACTION_LABELS: Record<string, string> = {
  buy: "Mua",
  rent: "Thuê",
  invest: "Đầu tư",
  other: "Khác",
};

export const KANBAN_STAGE_LABELS: Record<string, string> = {
  new: "Mới",
  contacted: "Đã liên hệ",
  viewing: "Đặt xem",
  negotiating: "Thương lượng",
  won: "Đã chốt",
  lost: "Đã mất",
};

export function labelFor(
  map: Record<string, string>,
  key: string | undefined
): string {
  if (!key) return "—";
  return map[key] || key;
}
