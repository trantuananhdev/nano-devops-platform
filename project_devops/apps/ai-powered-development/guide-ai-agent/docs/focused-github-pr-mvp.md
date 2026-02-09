# Focused MVP: AI Dev Agent for GitHub PR

Tài liệu này “đóng khung” hệ thống hiện tại theo 6 lớp của `@cursor-guide-digital-fte-platform`.

## 1) Luật (Law)
- Quy định “đáng tin” cho product là: **test exit code** trong sandbox.
- LLM chỉ được tạo **patch** (unified diff). Không có claim hoàn thành dựa trên cảm tính.
- Chặn ngôn ngữ ước đoán nằm ngoài diff (`should/probably/...`) để tránh nhúng vào comment/decision.
- Nếu `git apply` hoặc test fail: **loop lại coder** cho tới `maxAttempts`. Không có side-effects ngoài comment PR.

## 2) Bộ nhớ (Memory)
Trong MVP, “memory” nằm trong Postgres theo SSOT:
- `agent_tasks`: trạng thái task theo `tenant_id` + `repo` + `pr_head_sha`
- `tenant_memory`: lưu lessons/patterns ở cấp tenant (hiện tại record lesson khi verification pass)

Row-level isolation: mọi query đều scope theo `tenant_id`.

## 3) Kỹ năng (Skills)
Pipeline khớp với code:
- `fetchPrContext`: lấy PR và nội dung các file thay đổi từ GitHub
- `generatePatch`: OpenAI sinh unified diff patch
- `verifyTests`: chạy test thật trong sandbox và lấy `exitCode/stdout/stderr`
- `commentResult`: comment evidence lên PR
- `sessionEnd`: record evolution (lesson) khi verification pass

## 4) Tác tử (Agents)
V1 tập trung vào 1 “ai dev agent”, nhưng vẫn giữ ranh giới trách nhiệm:
- Coder prompt + patch extraction + apply
- QA/verification là gate chạy test thật (exit code là nguồn sự thật)
- GitHub side effects (comment) chỉ chạy ở cuối

## 5) Kiểm chứng (Verification)
- Verification = `npm test`/`yarn test`/`pnpm test` sau `install/ci`.
- Nếu fail: loop quay lại coder và re-run.

## 6) Tiến hóa (Evolution)
- Chỉ cập nhật lesson/pattern khi test pass để tránh “ghi nhận sai”.
- Mọi phiên chạy đều để lại evidence: stage/exitCode (trong comment + task result).

