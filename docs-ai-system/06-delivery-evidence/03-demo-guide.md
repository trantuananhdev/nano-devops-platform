# Demo Guide — vagrant up → Demo CEO trong 10 phút

> **Audience:** CEO, Sales, Demo Engineer
> **Mục đích:** Step-by-step guide để demo hệ thống từ scratch.

---

## Prerequisites

```bash
# Cần có:
- Vagrant + VMware Desktop (hoặc VirtualBox)
- Ubuntu machine cho LLM node (hoặc skip nếu dùng Gemini mock)
- .env file đã configure (copy từ .env.example)
```

---

## 10-Minute Demo Script

### Bước 1: Khởi động (2 phút)

```bash
# Terminal 1: Start VM và deploy
vagrant up                          # Khởi động Alpine VM (~1 phút)
./cli.sh ansible-deploy-llm         # Deploy Ubuntu LLM node (nếu có)
./cli.sh hdtv-up                    # Khởi động HDTV stack
./cli.sh hdtv-migrate               # Apply DB migrations
./cli.sh hdtv-seed                  # Seed demo data
./cli.sh hdtv-smoke                 # Verify: 4 checks pass
```

**Mở browser:**
- Frontend: `http://192.168.157.10:3080`
- API Docs: `http://192.168.157.10:8000/docs`
- Grafana: `http://192.168.157.10:3000`

---

### Bước 2: Demo cho CEO — Business Flow (5 phút)

**Scene 1: Upload hồ sơ**
```
1. Vào DossierList (màn hình chính)
2. Bấm "Tạo hồ sơ mới"
3. Điền: Tên dự án, Đơn vị (EVN Miền Nam), Loại (Mua sắm thiết bị)
4. Upload PDF scan hồ sơ
5. → Hệ thống confirm "Hồ sơ đã tạo, sẵn sàng thẩm định"
```

**Scene 2: AI Thẩm định Real-time**
```
1. Bấm "Thẩm định" trên hồ sơ vừa tạo
2. → Dashboard hiện progress bar
3. → Real-time events: "Lập kế hoạch...", "Đang kiểm tra ngân sách...",
       "Đang tra cứu pháp luật...", "Đang kiểm duyệt báo cáo..."
4. → Khoảng 30-60 giây: "Thẩm định hoàn tất"
5. → Risk badge hiện: 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW
```

**Scene 3: Xem báo cáo theo vai trò**
```
1. Login với tài khoản hdtv_leader (user_id=1)
   → Báo cáo: 1 trang tóm tắt, risk level đầu tiên
2. Login với tài khoản specialist (user_id=4)
   → Báo cáo: Full technical detail, tất cả checks
→ Cùng 1 hồ sơ, output khác nhau tùy người xem
```

**Scene 4: Alert cho CEO**
```
1. Vào màn hình Alerts
2. → Hồ sơ risk HIGH: alert đỏ, notification tự động
3. → Bấm "Resolve" sau khi xem xét
```

**Scene 5: Feedback → AI học**
```
1. Xem báo cáo xong, bấm 👎
2. Gõ comment: "Thiếu kiểm tra nhà thầu trong danh sách đen"
3. → Hệ thống confirm "Đã ghi nhận, AI sẽ học từ phản hồi này"
4. → Lần thẩm định tiếp theo: AI tự thêm bước kiểm tra nhà thầu
```

---

### Bước 3: Demo cho CTO — Technical Depth (3 phút)

**Scene 6: Audit Trail**
```
1. Vào Admin > Audit Logs
2. → Mỗi tool call: tool_name, execution_ms, inputs, outputs, plan_step_id
3. → Có thể trace: từ báo cáo cuối → từng bước agent thực hiện
4. → MCP Audit Logs tab: mọi external AI agent gọi tool đều có log
```

**Scene 7: Agent Intelligence**
```
1. Admin > Agent Intelligence tab
2. → 4 KPIs:
   - Plan Revision Rate: % lần agent cần revise plan
   - Critic Rejection Rate: % báo cáo bị quality gate reject
   - Total Feedback: số lần user phản hồi
   - Memory Retrieval Count: agent đã học bao nhiêu memories
```

**Scene 8: Observability**
```
1. Mở Grafana: http://192.168.157.10:3000
2. → Dashboard "HDTV AI Agent":
   - LLM health (circuit breaker state, latency)
   - Tool execution rate
   - Appraisal throughput
3. → 14 alert rules active
```

---

## Demo Data (Seeded)

```
Hồ sơ mẫu: 3 hồ sơ với risk level khác nhau
Users: 4 users (hdtv_leader, dept_head, admin, specialist)
Legal docs: ~50 chunks (nghị định, thông tư EVN)
Tools: 7 tools registered và active
Feedback: 5 feedbacks mẫu (AI đã học)
```

---

## Fallback nếu có sự cố

| Sự cố | Fix nhanh |
|-------|-----------|
| LLM node không connect | `./cli.sh hdtv-up` vẫn chạy — Gemini mock thay thế |
| Stack chưa start | `./cli.sh hdtv-smoke` xem service nào fail |
| DB migration fail | `./cli.sh hdtv-migrate` retry |
| Seed fail | `./cli.sh hdtv-seed` idempotent, retry OK |

---

## Key Messages cho CEO

> "Hệ thống xử lý tự động trong **30-60 giây** thay vì 2-3 ngày thẩm định thủ công."

> "AI **không tự quyết định** — khi không chắc, nó hỏi lại lãnh đạo (HITL). Con người vẫn là người quyết định cuối cùng."

> "Mọi hành động của AI đều được **ghi lại đầy đủ** — ai làm gì, lúc nào, kết quả gì. Audit trail hoàn chỉnh cho compliance."

> "Hệ thống **tự học từ phản hồi** — càng dùng càng tốt hơn."
