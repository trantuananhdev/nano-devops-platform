# CLAUDE.md (Guide Role Instruction)

Tài liệu này đóng vai trò “luật làm việc” mặc định cho mọi quá trình xây dựng Digital FTE Platform.
Nó không nói về nhiệm vụ cụ thể; nó định nghĩa cách làm việc để kết quả:
1) đúng sự thật,
2) ổn định,
3) có kiểm chứng,
4) có đường quay lui (rollback).

## Delivery Standards (không được vi phạm)

- **Truth > Speed**: ưu tiên đúng/đủ/được verify hơn là trả lời nhanh.
- **No “should/probably”**: không dùng ngôn ngữ mang tính ước đoán khi kết luận.
- **Self-verify trước khi tuyên bố hoàn thành**:
  - Liệt kê rõ tiêu chí “đủ tốt” cho từng claim quan trọng.
  - Nếu chưa verify được, phải nêu rõ “chưa chứng minh được bằng gì”.
- **Verification-first**: mọi thay đổi code/logic phải kèm một cách kiểm tra tối thiểu.
- **Rollback path**: mỗi thay đổi quan trọng phải nêu cách quay lui nếu hỏng (ví dụ: khôi phục flag config, revert commit, hoặc sử dụng fallback implementation).

## Execution Mode (cách làm)

- Tách công việc thành 3 bước: `Plan -> Execute -> Verify`.
- Khi gặp phạm vi mơ hồ, phải hỏi lại hoặc tạo “assumption list” rõ ràng (không giả định ngầm).
- Mọi cập nhật kiến trúc phải giữ được:
  - **API contract ổn định**
  - **Memory SSOT**
  - **Skill interface không bị phá vỡ**

## Enterprise Guardrails (khi áp dụng)

- Luôn phân biệt:
  - policy / rule
  - dữ liệu chuẩn vận hành (source of truth)
  - incident / lesson learned (không trộn với knowledge thông thường)
- Khi nhắc tới tích hợp hệ thống doanh nghiệp:
  - ghi rõ “dữ liệu nào được đọc/ghi”
  - ghi rõ “cổng human review” ở đâu
  - ghi rõ audit/log cần gì

## Đầu ra mong muốn

- Khi bạn trả lời hoặc viết code: phải kèm tối thiểu:
  - điều gì đã làm
  - tiêu chí verify
  - đường rollback nếu fail

