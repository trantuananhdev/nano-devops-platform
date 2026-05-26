# Kịch bản demo — Trung tâm tiếp nhận CRM TNT Shop

**Đối tượng:** Presenter / Trưởng phòng AI — thao tác **chỉ trên browser**.  
**UI:** `https://crm-demo.nano.platform`  
**Mô hình nghiệp vụ:** Một “trang” TNT (Fanpage + TikTok Shop + Shopee Official) — **đổ traffic** bằng kịch bản có sẵn → AI phân loại → hồ sơ khách → auto-reply hoặc cảnh báo Leader.

---

## Chuẩn bị

1. VM: `vagrant up` → `./cli.sh up`
2. **Hosts** máy presenter → IP VM: `crm-demo.nano.platform` (bắt buộc cho UI), `grafana.nano.platform` (tùy chọn).  
   `crm-ingest.nano.platform` chỉ cần cho curl/smoke — UI gọi API qua cùng host `crm-demo`.
3. Import `rootCA.crt` (HTTPS)
4. `.env`: `GEMINI_API_KEY`, optional Telegram

Mở Command Center → trạng thái **Sẵn sàng — đang lắng nghe inbox**.

### Vị trí demo multi-channel trên UI

1. **Thanh header —「Trung tâm đa kênh」**: 3 ô Facebook · TikTok · Shopee (badge MULTI-CHANNEL).
2. **Kịch bản đầu tiên —「★ Đa kênh đồng thời」**: 1 click → 3 tin 3 kênh vào cùng luồng.
3. **Cột trái —「Hoặc gửi lẻ từng kênh」**: 4 nút màu (FB / TikTok / Shopee / Inbox chung).

Nếu không thấy kịch bản: `./cli.sh redeploy crm-ingestion-api crm-demo-ui` (API `/api/v1/demo/scenarios`).

---

## Mở đầu (30 giây) — “chém gió”

> "TNT bán thời trang, mỹ phẩm, gia dụng ra Đông Nam Á. Một Fanpage và shop chính thức — traffic live, ads, flash sale **ập inbox** Tagalog, Indo, Malay. Trước đây 3 kênh rời, CS Việt Nam đuổi không kịp. Hôm nay **một trung tâm tiếp nhận**: đổ traffic thử, AI phân loại, tóm tắt tiếng Việt cho team, bot trả FAQ, tin hủy đơn báo Leader ngay."

Chỉ panel **Quy trình CRM TNT** (5 bước) và **AI giải quyết gì?**

---

## Trình diễn (chỉ UI)

| Phút | Thao tác | Nói (gợi ý) |
|------|----------|----------------|
| **0–2** | Chỉ **Trung tâm đa kênh** (header) | 3 inbox → 1 màn hình |
| **2–5** | **★ Đa kênh đồng thời** | Stream có FB + TikTok + Shopee xen kẽ |
| **5–7** | **1 tin khẩn** (tùy chọn) | Chargeback — ⏳ → 🤖 → 🚨 |
| **5–9** | **Đổ traffic Live TikTok** | 4 tin ID/TL hỏi giá — bot trả lời, metrics tăng |
| **9–12** | **Bão tin hủy đơn Facebook** | Không auto-reply — ticker đỏ, Telegram Leader |
| **12–15** | **Flash sale Shopee** | Malay COD/tracking — auto-reply |
| **15–17** | Chọn 1 dòng stream → **Chi tiết khách** | Tên, SĐT, đơn, tin gốc đa ngôn ngữ, tóm tắt AI |
| **17–19** | **ROI widget** | Tiết kiệm CS khi 65% tin bot xử lý |
| **19–21** | Grafana **CRM AI Pipeline** (tab khác) | Queue, LLM latency |

**Lưu ý:** Mỗi kịch bản đổ **nhiều tin** — đợi ~15–20s/tin (worker tuần tự). Không bấm 3 kịch bản chồng nhau.

---

## Kịch bản có sẵn (API `GET /api/v1/demo/scenarios`)

| ID | Tiêu đề |
|----|---------|
| `multi_channel_mix` | ★ Đa kênh đồng thời (FB + TikTok + Shopee) |
| `single_hot_lead` | 1 tin khẩn (demo nhanh) |
| `live_tiktok_surge` | Đổ traffic Live TikTok |
| `cancel_storm_facebook` | Bão tin hủy đơn Facebook |
| `shopee_flash_traffic` | Flash sale Shopee (MY) |
| `complaint_escalation` | Khiếu nại & đòi hoàn tiền |
| `positive_upsell_wave` | Sóng khách hài lòng & tái mua |

Đổ lô: `POST /api/v1/demo/traffic-burst` body `{"scenario_id":"live_tiktok_surge"}`.

---

## Quy trình CRM (nói khi chỉ pipeline)

1. **Tiếp nhận** — Webhook 3 kênh → Redis queue (không block khách)  
2. **Phân loại AI** — intent, urgency, sentiment, ngôn ngữ  
3. **Hồ sơ khách** — tên, SĐT, mã đơn, sản phẩm (LLM + metadata demo)  
4. **Hành động** — auto-reply inquiry hoặc escalate cancel/complaint  
5. **Đo lường** — Grafana, SLA, ROI

---

## Năng lực AI (nói khi panel phải)

- **Đa ngôn ngữ SEA** — CS đọc summary, không cần thuê 3 team ngôn ngữ  
- **Triage 24/7** — cancel/chargeback lên Leader trong giây  
- **Trả lời có kiểm soát** — không auto-refund khiếu nại  
- **Một Command Center** — thay 3 app inbox

---

## Smoke (trên VM)

```bash
bash project_devops/platform/ops/smoke-tests/smoke-test-crm-demo.sh
bash project_devops/platform/ops/smoke-tests/smoke-test-crm-ingestion.sh
```

Redeploy sau đổi code:

```bash
./cli.sh redeploy crm-ingestion-api crm-ai-worker crm-demo-ui
```
