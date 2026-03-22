# Memory SSOT (chuẩn hóa cho Digital FTE)

## Nguyên tắc
- **SSOT (Single Source of Truth)**: mỗi loại thông tin có đúng 1 nơi để cập nhật.
- Tránh “một sự thật, nhiều bản sao” làm sai lệch trạng thái.
- Lưu cả:
  - trạng thái hiện tại (operational state)
  - lịch sử/lesson learned (evidence for evolution)

## Gợi ý cấu trúc memory tối thiểu (cá nhân / MVP)
- `memory/today.*`  
  - đang làm gì, vướng gì, bước tiếp theo
- `memory/projects.*`  
  - mục tiêu, scope, quyết định quan trọng, trạng thái dự án
- `memory/patterns.*`  
  - mẫu hình xử lý lặp lại (re-usable)
- `memory/active-tasks.json`  
  - task nào đang active/blocked/waiting

## Gợi ý cho doanh nghiệp (quy hoạch nâng cấp)
- `policy/` (AI access, hành động được phép, human review gate)
- `sop/` (workflow chuẩn từng phòng ban)
- `incident-log/` (failure mode + lesson learned)
- `case-library/` (case resolved)
- `backlog/` (các cải tiến đề xuất)
- `handoff/` (chuẩn trao tay giữa người và agent)

## Checklist SSOT khi tích hợp hệ thống
- Xác định “dữ liệu chuẩn” nằm ở đâu.
- Xác định agent nào được đọc/được ghi.
- Xác định cổng verification/human approval.
- Xác định log/audit yêu cầu gì (để audit được).

