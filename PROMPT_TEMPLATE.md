# Prompt Template cho AI Assistant — HDTV Platform

## Cách dùng prompt này
Sao chép toàn bộ và gửi cho AI assistant mỗi khi bạn muốn tiếp tục phát triển.

---

```markdown
@ai-system/AI_BOOT.md
@ai-system/HDTV_PHASE12_TASKS.md
@ai-system/PROJECT_STATE.md
@ai-system/final_ai_context.md
@ai-system/final_devops_context.md

Đọc boot sequence trong AI_BOOT.md.

Thực hiện task PENDING đầu tiên trong HDTV_PHASE12_TASKS.md (theo thứ tự ưu tiên).

### Lưu ý quan trọng
1. **Không hỏi tôi từng dòng code** — tự tìm hiểu và code
2. **Không cần chạy test** — tôi chưa bật VM, chỉ cần code chất lượng
3. **Tuân theo quy ước code hiện tại** — xem các file cũ để follow style
4. **Topology 2 máy**: Ubuntu = LLM only, Alpine = app stack
5. **LLM qua HTTP** — không embed vào FastAPI
6. **Mọi tool call ghi ai_audit_logs**
7. **FE không đổi CSS variables / .glass-panel**
8. **Focus vào workflow và chất lượng code**

Sau khi xong:
1. Chạy verify_cmd của task (nếu có)
2. Self-critique theo SELF_CRITIQUE.md
3. Cập nhật PROJECT_STATE.md và HDTV_PHASE12_TASKS.md
4. Báo cáo ngắn: đã làm gì, demo được gì, blocker (nếu có)
```


