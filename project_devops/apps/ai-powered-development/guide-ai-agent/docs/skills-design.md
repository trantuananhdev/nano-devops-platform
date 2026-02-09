# Skills Design (mỗi skill là năng lực hành động)

## Mục tiêu của skill
Skill không phải “chứa kiến thức”, mà là **thao tác có quy trình** để tạo output đáng tin.

## Template tối thiểu cho một skill
- **Goal**: skill tạo ra cái gì (định nghĩa “đủ tốt”).
- **Trigger**: khi nào gọi skill này.
- **Inputs**: loại dữ liệu cần.
- **Process**: các bước tuần tự (không bỏ qua verification).
- **Outputs**: format trả về (có thể parse được).

## Quy tắc không gom nhầm
- Skill không nên “hỗ trợ mọi thứ”.
- Skill càng đúng một job-to-be-done, test/verify càng dễ.

## Nhóm skill khởi đầu cho Digital FTE (gợi ý)
- Skill điều phối: lập kế hoạch -> chia task -> handoff
- Skill kiểm tra: fact check / policy check / qa structure
- Skill thực thi SOP: chạy workflow theo playbook
- Skill tiến hóa: ghi lesson learned -> cập nhật patterns/rules
- Skill rollback: tạo fallback khi verification fail

