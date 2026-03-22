# Task Routing & Agents (phối hợp đúng vai)

## Agent không theo “tên”
Agent phải theo ranh giới trách nhiệm:
- Tôi chịu trách nhiệm phần nào?
- Tôi không được làm phần nào?
- Tôi phải gọi skill/agent nào khi nào?
- Tôi escalate sang người khi nào?

## Digital FTE Platform: gợi ý pipeline
1. `Agent Intake` tiếp nhận yêu cầu từ human/system
2. `Router Agent` phân loại task theo type + policy
3. `SOP Executor Agent` thực thi playbook theo skill
4. `QA/Verification Agent` chạy verification gate
5. `Report Synthesizer` tổng hợp output + evidence + decision
6. `Lifecycle Manager` cập nhật memory + active-tasks + escalation

## Output chuẩn để agents phối hợp
Mỗi bước phải trả về ít nhất:
- `claims` (điều gì được đề xuất/kết luận)
- `evidence` (bằng chứng/kiểm tra nào tạo ra claims)
- `verification_status` (pass/fail + lý do)
- `rollback_plan` nếu fail

