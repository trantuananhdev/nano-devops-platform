/** Nhãn tiếng Việt — demo CRM Bất động sản đa kênh */

export const VI = {
  appTitle: "Trung tâm điều hành CRM BĐS",
  appSubtitle:
    "Tiếp nhận đa kênh → AI phân loại nhu cầu → pipeline sales · cảnh báo khẩn",

  workflow: {
    title: "Quy trình demo cho sale & CS",
    subtitle:
      "Mô phỏng luồng khách thật: đổ traffic hoặc gửi lẻ từng kênh, theo dõi AI xử lý, chuyển giai đoạn trên Kanban.",
    steps: [
      {
        title: "Kích hoạt traffic",
        desc: "Chọn kịch bản bên trái hoặc gửi 1 tin thử từ Facebook / Zalo / TikTok.",
      },
      {
        title: "Theo dõi AI",
        desc: "Xem luồng tin, summary burst và cảnh báo lead khẩn trong ~20 giây.",
      },
      {
        title: "Chốt nghiệp vụ",
        desc: "Chuyển tab Pipeline — kéo thả lead theo giai đoạn tư vấn BĐS.",
      },
    ],
  },

  tabs: {
    traffic: "Điều hành traffic",
    crm: "Pipeline bán hàng",
  },

  status: {
    connecting: "Đang kết nối luồng realtime…",
    live: "Sẵn sàng — đang lắng nghe inbox",
    queued: "Đã tiếp nhận — AI xếp hàng",
    queuedDepth: (n: number) => `Hàng đợi ${n} tin — worker đang xử lý`,
    processing: "AI đang phân tích…",
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
    title: "Trung tâm đa kênh BĐS",
    subtitle: "Facebook · Zalo · TikTok → một pipeline CRM",
    sendOne: "Gửi thử 1 tin / kênh (tối đa 3 tin/kịch bản)",
    emptyScenarios: "Không tải được kịch bản — redeploy crm-ingestion-api hoặc dùng nút kênh bên dưới.",
    count24h: (ch: string, n: number) => `${ch}: ${n} tin (24h)`,
  },

  trafficPanel: {
    title: "Kịch bản đổ traffic",
    hint: "Mỗi lần chạy tối đa 3 tin — phù hợp demo trước khách. Sau burst, Agent Traffic tổng hợp báo cáo.",
    singleTitle: "Gửi thử từng kênh",
  },

  trafficSummary: {
    title: "Báo cáo burst — Agent Traffic",
    empty: "Chưa có báo cáo",
    emptyHint: "Chạy một kịch bản traffic để AI tổng hợp kênh, lead nóng và việc cần làm.",
    loading: "Đang tổng hợp sau burst…",
    hotLeads: "Lead cần gọi ngay",
    channels: "Phân bổ kênh",
    recommendations: "Việc ưu tiên cho sale",
  },

  crm: {
    kanbanHint: "Kéo thả thẻ lead giữa các cột — đồng bộ giai đoạn tư vấn BĐS.",
    noLeadSelected: "Chọn lead trên board để xem hồ sơ, hoạt động và cơ hội.",
    pipelineStatus: "Giai đoạn tư vấn",
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
    title: "6 AI Agent phân vai",
    items: [
      {
        icon: "📊",
        title: "Agent 1 — Traffic",
        desc: "Tổng hợp sau mỗi burst: kênh, hot leads, khuyến nghị cho team sales.",
      },
      {
        icon: "🏢",
        title: "Agent 2 — CRM Extract",
        desc: "Phân loại BĐS (căn hộ, đất, shophouse), ngân sách, intent — auto-reply FAQ.",
      },
      {
        icon: "👔",
        title: "Agent 3 — Trưởng phòng",
        desc: "Brief vận hành ngắn gọn cho manager khi lead vào pipeline.",
      },
      {
        icon: "🛡️",
        title: "Agent 6 — Compliance",
        desc: "Chặn cam kết ROI / pháp lý; flag tin nhạy cảm trước khi gửi khách.",
      },
    ],
  },

  stream: {
    title: "Hộp thư lead realtime",
    count: (n: number) => `${n} lead`,
    empty: "Chưa có lead trong phiên demo.",
    emptyHint: "Bước 1: chọn kịch bản traffic hoặc gửi tin thử từ một kênh.",
    waiting: "Chờ AI phân tích…",
    queued: "Đang xếp hàng",
    processing: "AI đang xử lý",
  },

  detail: {
    title: "Hồ sơ khách hàng",
    emptyTitle: "Chưa chọn lead",
    emptyHint:
      "Nhấn một dòng trong hộp thư bên trái để xem nhu cầu BĐS, ý định và gợi ý xử lý từ AI.",
    emptyAction: "Chọn lead từ danh sách",
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
    waitingAi: "AI đang trích xuất intent, urgency, sentiment và tóm tắt cho CS.",
    autoReply: "Trả lời tự động",
    alert: (t?: string) => `Đã báo Leader (${t || "hot_lead"})`,
  },

  alerts: {
    title: "Cảnh báo khẩn (24h)",
    empty: "Chưa có cảnh báo — thử kịch bản compliance hoặc lead khẩn.",
  },

  roi: {
    title: "ROI vận hành CS BĐS",
    staff: "Nhân sự tư vấn",
    salary: "Lương TB (triệu VND/tháng)",
    messages: "Lead/ngày (đa kênh)",
    autoRate: "Tỷ lệ AI xử lý FAQ",
    result: (usd: number, hrs: number) =>
      `~${usd.toLocaleString("vi-VN")} triệu/tháng · tiết kiệm ~${Math.round(hrs)} giờ/ngày`,
    disclaimer:
      "Mô hình minh họa CRM BĐS — chỉnh slider theo số liệu thực tế khi triển khai.",
  },

  channels: {
    facebook: "Facebook",
    tiktok: "TikTok",
    zalo: "Zalo OA",
    instagram: "Instagram",
    shopee: "Shopee",
    generic: "Website / Inbox",
  },
} as const;

export function intentVi(intent: string): string {
  const map: Record<string, string> = {
    queued: "Chờ tiếp nhận",
    processing: "Đang phân tích",
    purchase: "Mua",
    inquiry: "Tư vấn",
    schedule_viewing: "Đặt xem",
    price_inquiry: "Hỏi giá",
    legal_inquiry: "Pháp lý",
    complaint: "Phàn nàn",
    cancel_order: "Hủy đơn",
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
