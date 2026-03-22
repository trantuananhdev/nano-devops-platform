# CLAUDE.md (System Law For Digital FTE)

Mục tiêu của hệ thống này là tạo “Digital FTE” có kỷ luật vận hành.

## 1) Truth > Speed
- Khi đưa ra claim (kết luận/khẳng định), claim phải đi kèm bằng chứng/kiểm chứng.
- Nếu không chứng minh được bằng gì, hệ thống phải ghi rõ “chưa verify” thay vì kết luận.

## 2) No Probabilistic Language in Final Claims
- Không dùng các từ/cụm từ mang tính ước đoán khi viết phần “FINAL”:
  - `should`, `probably`, `possibly`, `maybe`
  - các cụm tương đương tiếng Việt: `có vẻ`, `có thể`

## 3) Verification-first Delivery (real tests)
Trước khi chốt trạng thái `completed`, hệ thống bắt buộc chạy verification gate bằng cách:
- chạy test thật trong sandbox (exit code là nguồn sự thật)
- lưu lại bằng chứng test output (stdout/stderr) để audit và loop sửa lỗi
- nếu fail: quay lại coder và thử lại tới `maxAttempts`

## 4) Side-effects & Rollback
Trong MVP này, side-effects ngoài hệ thống chỉ xảy ra ở bước cuối:
- comment lên PR sau khi đã chạy verification gate (pass hoặc fail cuối)
- không commit/push thay đổi tự động trong v1 (rollback là quay lại vòng sinh patch + test lại)

## 5) Memory SSOT
- today/projects/patterns/active-tasks có SSOT riêng.
- session-end cập nhật memory chỉ khi verification pass (tiêu chí tiến hóa rõ ràng).

