/** Nhãn tiếng Việt — demo TNT Shop (trung tâm tiếp nhận đa kênh) */

export const VI = {
  appTitle: "TNT Shop — Trung tâm tiếp nhận CRM",
  appSubtitle:
    "Một Fanpage / TikTok Shop / Shopee Official → đổ traffic → AI phân loại · trả lời · cảnh báo",

  status: {
    connecting: "Đang kết nối luồng realtime…",
    live: "Sẵn sàng — đang lắng nghe inbox",
    queued: "Đã tiếp nhận — AI xếp hàng",
    queuedDepth: (n: number) => `Hàng đợi ${n} tin — worker đang xử lý`,
    processing: "Gemini đang phân tích…",
    autoReply: "Đã gửi trả lời tự động — hoàn tất…",
    processed: "Đã xử lý xong",
    sending: (name: string) => `Đang đổ kịch bản: ${name}…`,
    burstDone: (n: number) => `Đã đổ ${n} tin — theo dõi luồng bên phải`,
    duplicate: "Tin trùng — bấm kịch bản khác",
    error: "Lỗi kết nối API",
    pollFallback: "Dự phòng polling — kiểm tra API",
  },

  metrics: {
    processed1h: "Xử lý (1h)",
    processed24h: "Xử lý (24h)",
    alerts24h: "Cảnh báo (24h)",
    autoReplies: "Trả lời tự động",
    hot1h: "Tin khẩn (1h)",
  },

  multiChannel: {
    title: "Trung tâm đa kênh",
    subtitle: "3 inbox → 1 Command Center (webhook thống nhất)",
    sendOne: "Gửi thử 1 tin / kênh",
    emptyScenarios: "Không tải được kịch bản — redeploy crm-ingestion-api hoặc dùng nút kênh bên dưới.",
    count24h: (ch: string, n: number) => `${ch}: ${n} tin (24h)`,
  },

  trafficPanel: {
    title: "Đổ traffic (kịch bản)",
    hint: "Kịch bản có nhãn FB · TikTok · Shopee — bấm ★ Đa kênh để demo multi-channel rõ nhất.",
    singleTitle: "Hoặc gửi lẻ từng kênh",
  },

  pipeline: {
    title: "Quy trình CRM TNT",
    steps: [
      { id: 1, label: "Tiếp nhận", desc: "Webhook Fanpage / TikTok / Shopee → hàng đợi Redis" },
      { id: 2, label: "Phân loại AI", desc: "Intent · urgency · sentiment · ngôn ngữ" },
      { id: 3, label: "Hồ sơ khách", desc: "Tên · SĐT · đơn hàng · sản phẩm quan tâm" },
      { id: 4, label: "Hành động", desc: "Auto-reply FAQ hoặc escalate Leader" },
      { id: 5, label: "Đo lường", desc: "Grafana · SLA · ROI CS" },
    ],
  },

  ai: {
    title: "AI giải quyết gì?",
    items: [
      {
        icon: "🌐",
        title: "Đa ngôn ngữ SEA",
        desc: "Tagalog, Bahasa, Malay, English — CS Việt Nam đọc tóm tắt tiếng Việt qua summary.",
      },
      {
        icon: "⚡",
        title: "Triage 24/7",
        desc: "Tin hủy đơn / chargeback lên Leader trong giây; tin hỏi giá được bot trả lời ngay.",
      },
      {
        icon: "🤖",
        title: "Trả lời tự động có kiểm soát",
        desc: "Chỉ auto-reply inquiry/purchase thường — không hứa refund với complaint/cancel.",
      },
      {
        icon: "📊",
        title: "Một màn hình điều phối",
        desc: "Thay vì 3 app inbox rời — Command Center gom stream + cảnh báo + ROI.",
      },
    ],
  },

  stream: {
    title: "Luồng tin realtime",
    empty: "Chọn kịch bản bên trái để mô phỏng traffic ập vào…",
    waiting: "Chờ AI…",
    queued: "⏳ chờ xử lý",
    processing: "🤖 AI",
  },

  detail: {
    title: "Chi tiết khách & AI",
    empty: "Chọn một dòng trong luồng tin để xem hồ sơ.",
    customer: "Khách hàng",
    message: "Tin nhắn gốc (đa ngôn ngữ)",
    summary: "Tóm tắt AI",
    intent: "Ý định",
    urgency: "Mức độ",
    sentiment: "Cảm xúc",
    channel: "Kênh",
    order: "Mã đơn",
    phone: "Điện thoại",
    product: "Sản phẩm quan tâm",
    locale: "Ngôn ngữ / locale",
    waitingQueue: "Tin đã vào hàng đợi — worker CRM sẽ phân tích trong ~15–20 giây.",
    waitingAi: "Gemini đang trích xuất intent, urgency, sentiment và tóm tắt cho CS.",
    autoReply: "Trả lời tự động (Gemini)",
    alert: (t?: string) => `Đã báo Leader (${t || "hot_lead"})`,
  },

  alerts: {
    title: "Cảnh báo khẩn (24h)",
    empty: "Chưa có cảnh báo — thử kịch bản hủy đơn / khiếu nại.",
  },

  roi: {
    title: "ROI vận hành CS",
    staff: "Nhân sự CS",
    salary: "Lương TB (USD/tháng)",
    messages: "Tin/ngày (cả 3 kênh)",
    autoRate: "Tỷ lệ bot xử lý",
    result: (usd: number, hrs: number) =>
      `~$${usd.toLocaleString("vi-VN")}/tháng · tiết kiệm ~${Math.round(hrs)} giờ/ngày`,
    disclaimer:
      "Mô hình minh họa cho demo TNT — chỉnh slider theo số liệu thực tế khi triển khai.",
  },

  channels: {
    facebook: "Facebook Page",
    tiktok: "TikTok Shop",
    shopee: "Shopee Mall",
    generic: "Website / Inbox chung",
  },
} as const;

export function intentVi(intent: string): string {
  const map: Record<string, string> = {
    queued: "Chờ tiếp nhận",
    processing: "Đang phân tích",
    purchase: "Mua hàng",
    inquiry: "Hỏi đáp",
    cancel_order: "Hủy đơn",
    complaint: "Khiếu nại",
    praise: "Khen ngợi",
    other: "Khác",
  };
  return map[intent] || intent;
}

export function urgencyVi(u: string): string {
  const map: Record<string, string> = {
    low: "Thấp",
    medium: "Trung bình",
    high: "Cao",
    critical: "Khẩn cấp",
    pending: "—",
  };
  return map[u] || u;
}

export function sentimentVi(s: string): string {
  const map: Record<string, string> = {
    positive: "Tích cực",
    neutral: "Trung lập",
    negative: "Tiêu cực",
    pending: "—",
  };
  return map[s] || s;
}
