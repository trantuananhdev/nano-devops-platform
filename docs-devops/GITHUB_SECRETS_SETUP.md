# GitHub Secrets Setup — EcoIT CD Pipeline

Cần thêm các secrets sau vào GitHub repo:
`Settings → Secrets and variables → Actions → New repository secret`

## Required Secrets

| Secret name | Giá trị | Ghi chú |
|-------------|---------|---------|
| `ACER_HOST` | `192.168.100.26` | IP Acer Ubuntu trên LAN |
| `ACER_USER` | `tutinhhao` | Linux user trên Acer |
| `ACER_SSH_PORT` | `22` | SSH port |
| `ACER_SSH_KEY` | Nội dung file `.ssh/prod_key` | Private key SSH vào Acer |
| `ECOIT_POSTGRES_PASSWORD` | Password DB | Không dùng default |
| `JWT_SECRET` | 32+ char random string | `python -c "import secrets; print(secrets.token_hex(32))"` |

## Optional Secrets

| Secret name | Mục đích |
|-------------|---------|
| `GEMINI_API_KEY_1` | Nếu bài toán cần AI |
| `OPENAI_API_KEY` | Nếu bài toán cần OpenAI |

## GitHub Environment Protection (khuyến nghị)

1. `Settings → Environments → New environment` → đặt tên `production`
2. Thêm `Required reviewers` = bản thân
3. CD workflow sẽ pause và chờ approval trước khi deploy

## SSH Key Setup (nếu chưa có)

```powershell
# Windows — tạo key pair
ssh-keygen -t ed25519 -C "ecoit-deploy" -f .ssh/prod_key

# Copy public key lên Acer Ubuntu
type .ssh\prod_key.pub | ssh tutinhhao@192.168.100.26 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

Sau đó copy nội dung `.ssh/prod_key` (private key) vào GitHub secret `ACER_SSH_KEY`.
