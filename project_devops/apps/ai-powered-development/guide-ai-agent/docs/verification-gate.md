# Verification Gate (đưa AI từ “thuyết phục” thành “đáng tin”)

## Nguyên tắc
- Không “claim complete” nếu chưa chứng minh được.
- Verification gate phải:
  - có tiêu chí đủ điều kiện (required fields)
  - kiểm tra output có vi phạm policy không
  - kiểm tra dữ liệu có khớp source-of-truth không (nếu có)
  - có audit log (để doanh nghiệp truy xuất)

## Red flags cần loại bỏ
- Dùng “should/probably/possibly”
- Báo cáo dựa trên kiểm tra một phần nhưng kết luận toàn bộ
- Không có log/không có chứng cứ (evidence)

## Rollback trong verification
- Khi verification fail, hệ thống phải:
  - dừng tuyên bố hoàn thành
  - kích hoạt fallback route (ví dụ: yêu cầu human review, hoặc chạy lại theo strategy khác)
  - ghi incident log để cải tiến về sau

