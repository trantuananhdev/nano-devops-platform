# AI-Powered Development (Core Agent)

This is the core AI Dev Agent responsible for fixing GitHub Pull Requests automatically.

- Nhận webhook GitHub cho `pull_request`
- AI Dev Agent đọc code thay đổi
- Áp dụng patch (unified diff) do OpenAI sinh
- **Verification gate chạy test thật** (`npm test`/`yarn test`/`pnpm test` theo lockfile)
- Nếu fail: loop sửa và chạy test lại tới tối đa `AGENT_MAX_ATTEMPTS`
- Comment kết quả lên PR

## Run bằng Docker

```bash
cd C:\\TA-work\\agentic1\\digital-fte-platform
docker compose up --build
```

## Setup (MVP)

1. Mint JWT (admin) cho tenant:
```bash
curl -s -X POST http://localhost:3000/v1/auth/token ^
  -H "x-admin-api-key: change-me-admin" ^
  -H "content-type: application/json" ^
  -d "{\"tenantId\":\"tenant-1\",\"userId\":\"admin-1\",\"role\":\"admin\"}"
```

2. Đăng ký GitHub repo + token cho tenant:
```bash
curl -s -X POST http://localhost:3000/v1/admin/github-repo ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -H "content-type: application/json" ^
  -d "{\"repoFullName\":\"OWNER/REPO\",\"githubToken\":\"<PAT_or_TOKEN>\"}"
```

3. Cấu hình webhook GitHub:
- URL: `http://<host>:3000/v1/webhooks/github`
- Secret: `GITHUB_WEBHOOK_SECRET` (bắt buộc trong prod; compose đã set sẵn 1 giá trị mẫu)
- Event: `pull_request` (opened, synchronize, reopened, edited)

## Xem task state
```bash
curl -s http://localhost:3000/v1/tasks/<taskId> ^
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```


