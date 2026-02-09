# Framework 6 Lớp (áp vào Digital FTE Platform)

## 1) Lớp Luật (Law)
- Định nghĩa **cách làm việc** cho agent/system (không phải nhiệm vụ).
- Output policy: không kết luận kiểu “có vẻ/chắc/chắc chắn/ probably”.
- Có **verification gate** trước khi “hoàn thành”.
- Có **rollback path** cho thay đổi có rủi ro.

## 2) Lớp Bộ nhớ (Memory)
- SSOT: mỗi loại thông tin chỉ có một nơi chuẩn để đọc/ghi.
- Memory tối thiểu (cá nhân): `today`, `projects`, `patterns`, `active-tasks`.
- Memory cho doanh nghiệp: SOP, policy, incident log, case library, backlog cải tiến, handoff.

## 3) Lớp Kỹ năng (Skills)
- Skill là “job to be done” có cấu trúc.
- Mỗi skill tối thiểu có:
  - Mục tiêu rõ
  - Trigger rõ
  - Input rõ
  - Quy trình tuần tự
  - Output rõ (format)

## 4) Lớp Tác tử (Agents)
- Agent = vai trò/chuyên môn hóa + ranh giới trách nhiệm.
- Agent giỏi không phải “biết mọi thứ”; agent giỏi là biết:
  - tôi chịu trách nhiệm phần nào
  - tôi không được làm phần nào
  - tôi phải gọi skill nào/agent nào khác khi nào

## 5) Lớp Kiểm chứng (Verification)
- Biến claim thành “đã được chứng minh”.
- Red flags: “should/probably”, kiểm tra một phần mà tuyên bố toàn bộ, thiếu log/audit.
- Gate doanh nghiệp: output đủ field bắt buộc + tuân policy + có audit log + có human approval khi cần.

## 6) Lớp Tiến hóa (Evolution)
- Mỗi phiên phải tạo “tài sản” có thể tái sử dụng:
  - lesson learned, checklist, pattern, rule mới, skill mới…
- Nếu không có tài sản để kế thừa, hệ chỉ đang tiêu hao token, không tiến hóa.

