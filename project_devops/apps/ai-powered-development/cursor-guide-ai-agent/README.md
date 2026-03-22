# Cursor Guide: Digital FTE Platform (6 Lớp)

Mục tiêu của folder này là giúp Cursor (và team) xây một hệ “Digital FTE Platform” theo đúng kỷ luật vận hành của Claude Code Framework:

- **Luật**: định nghĩa “cách làm việc” trước khi làm việc
- **Bộ nhớ**: SSOT + nhiều tầng để không reset mỗi phiên
- **Kỹ năng**: mỗi skill là một năng lực có cấu trúc, có input/output rõ ràng
- **Tác tử**: chuyên môn hóa theo vai và ranh giới trách nhiệm
- **Kiểm chứng**: verification gate biến đầu ra thành “đáng tin”
- **Tiến hóa**: mỗi phiên để lại tài sản có thể tái sử dụng

## Cách dùng

1. Mở `cursor-guide-digital-fte-platform/CLAUDE.md` để đọc “luật giao tiếp” mặc định cho mọi thay đổi code.
2. Đọc lần lượt các tài liệu trong `docs/` (6-layers -> memory -> skills -> verification -> routing/agents).
3. Tham chiếu thêm `docs/focused-github-pr-mvp.md` để thấy mapping 6 lớp vào đúng product MVP hiện tại.
3. Khi xây system thực tế, tham chiếu vào folder `digital-fte-platform/` (skeleton chạy được).

## Nguyên tắc “dễ tích hợp / dễ nâng cấp”

- Tách rõ **policy/rules** với **orchestration logic** với **skill library**.
- File hóa rõ “SSOT” cho memory: dữ liệu chuẩn ở đâu, policy ở đâu, incident/lesson ở đâu.
- Verification gate là cơ chế chung, không phụ thuộc provider (LLM hay non-LLM).

