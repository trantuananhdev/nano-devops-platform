# CI/CD Pipeline — GitOps, Build, Deploy

> **Audience:** CTO, DevOps Engineer
> **Mục đích:** GitOps flow từ commit đến production — lint, build, test, deploy.

---

## GitOps Principle

```
Developer / AI
    ↓ git commit + PR
Git Repository (GitHub)
    ↓ trigger on push/PR
CI Pipeline (GitHub Actions)
    ↓ lint → build → test → package
Container Registry (GHCR)
    ↓ image tag: sha-abc123
CD Script (cli.sh)
    ↓ pull image → health check → switch traffic
Docker Runtime (Alpine VM)
```

**Không bao giờ** sửa file trực tiếp trên VM. Mọi thay đổi phải qua Git.

---

## CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
jobs:
  build-hdtv:
    steps:
      - name: Lint
        run: |
          pip install ruff
          ruff check app/

      - name: Build image
        run: |
          docker build -t hdtv-ai-platform:${{ github.sha }} .
          docker build -f Dockerfile.worker -t hdtv-worker:${{ github.sha }} .

      - name: Static tests
        run: |
          pip install pytest
          pytest tests/test_static.py -v  # 13 offline cases

      - name: Security scan
        run: |
          pip install gitleaks
          gitleaks detect --no-git  # Scan for secrets in code

      - name: Push to registry
        run: |
          docker push ghcr.io/org/hdtv-ai-platform:${{ github.sha }}
          docker push ghcr.io/org/hdtv-worker:${{ github.sha }}
```

---

## Deploy (cli.sh)

```bash
# Tất cả operations qua cli.sh — single entry point
./cli.sh hdtv-up          # docker compose up với canonical file
./cli.sh hdtv-migrate     # alembic upgrade head
./cli.sh hdtv-seed        # seed DB + Chroma + Meilisearch
./cli.sh hdtv-smoke       # 4 smoke checks
./cli.sh hdtv-backup      # backup PG + MinIO + Chroma
./cli.sh obs-up           # start observability stack
./cli.sh ansible-deploy-llm  # deploy Ubuntu LLM node
```

---

## Immutable Deployment

```bash
# deploy: không patch container đang chạy
docker compose pull hdtv-api          # Pull new image
docker compose up -d hdtv-api        # Rolling replace (new container)
# → Traefik tự route sang container mới sau health check
# → Không có downtime (container cũ vẫn chạy cho đến khi new healthy)
```

---

## DORA Metrics Target

| Metric | Target | Hiện tại |
|--------|--------|---------|
| Deployment frequency | Daily | On-demand |
| Lead time for change | < 1 day | < 4 hours |
| MTTR | < 1 hour | < 2 hours (manual) |
| Change failure rate | < 15% | ~5% (smoke test gate) |
