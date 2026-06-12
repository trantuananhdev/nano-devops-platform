# Giai đoạn 3 — Enterprise Scale (2027+)

> **Audience:** CTO, CEO, Solution Architect
> **Mục đích:** Scale lên 10+ clients, air-gapped hoàn toàn, multi-tenant, HA cluster, fine-tuned models theo domain.

---

## 1. Mục tiêu giai đoạn

| Dimension | Giai đoạn 2 | Giai đoạn 3 (Enterprise) |
|-----------|------------|--------------------------|
| Clients | 3-5 | 10+ (nhiều tổ chức, nhiều ngành) |
| Users/ngày | 50-200 | 1,000-5,000 |
| Dossier/ngày | 200-500 | 2,000-10,000 |
| LLM | Hybrid (local ưu tiên) | **100% Air-gapped — KHÔNG dùng internet** |
| Infrastructure | 5-10 nodes | K8s cluster hoặc bare-metal GPU cluster |
| Model | General model (Gemma/Llama) | **Fine-tuned domain-specific models** |
| Data isolation | Per-schema | Per-namespace K8s + dedicated storage |
| Compliance | Basic audit logs | Full audit trail, data residency, SOC2-ready |

---

## 2. Kiến trúc Enterprise

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  AIR-GAPPED PERIMETER — Không có kết nối internet nào từ AI/LLM layer       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  KUBERNETES CLUSTER (on-prem / private cloud)                       │    │
│  │                                                                     │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  GPU NODE POOL (LLM Inference)                               │   │    │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │    │
│  │  │  │ vLLM Replica1│  │ vLLM Replica2│  │  vLLM Replica3   │   │   │    │
│  │  │  │ Qwen 2.5 72B │  │ Qwen 2.5 72B │  │ Legal-fine-tuned │   │   │    │
│  │  │  │ (4× A100 40G)│  │ (4× A100 40G)│  │ (2× A100 40G)    │   │   │    │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────┘   │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                     │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  CPU NODE POOL (Application)                                 │   │    │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │    │
│  │  │  │FastAPI   │ │FastAPI   │ │FastAPI   │ │ Worker Pool    │  │   │    │
│  │  │  │Pod (×3)  │ │Pod (×3)  │ │Pod (×3)  │ │ (×10 workers)  │  │   │    │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                     │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  DATA NODE POOL (Stateful)                                   │   │    │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │    │
│  │  │  │PostgreSQL│ │Redis     │ │Chroma    │ │MinIO           │  │   │    │
│  │  │  │HA Cluster│ │Cluster   │ │Cluster   │ │Distributed     │  │   │    │
│  │  │  │(3 nodes) │ │(3 nodes) │ │(3 nodes) │ │(6 nodes)       │  │   │    │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                     │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  OBSERVABILITY STACK                                         │   │    │
│  │  │  Prometheus Thanos │ Grafana Enterprise │ Loki │ Jaeger      │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  EDGE LAYER (Ingress)                                               │    │
│  │  Istio Service Mesh │ Kong API Gateway │ TLS termination            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↕
                        [Intranet / VPN only]
                                    ↕
                            Client organizations
```

---

## 3. Air-gapped LLM — Tại sao bắt buộc ở giai đoạn này

Khi hệ thống xử lý dữ liệu nhạy cảm của nhiều tổ chức lớn (EVN, cơ quan nhà nước, ngân hàng...), việc gửi dữ liệu ra internet **không thể chấp nhận được**:

| Rủi ro | Hệ quả |
|--------|--------|
| Dữ liệu hồ sơ thẩm định gửi qua Gemini API | Vi phạm bảo mật thông tin, quy định nội bộ |
| Phụ thuộc Google/Gemini uptime | Hệ thống ngừng hoạt động khi API down |
| Chi phí API scale theo volume | Không dự đoán được chi phí khi 10,000 hồ sơ/ngày |
| Latency mạng ngoài | Ảnh hưởng SLA thẩm định real-time |
| Data residency requirements | Dữ liệu EVN/nhà nước phải nằm trong nước |

**Kết luận:** Giai đoạn 3 bắt buộc 100% local LLM. Chi tiết xem `04-airgap-llm-strategy.md`.

---

## 4. Fine-tuned Domain Models

Thay vì dùng general model, enterprise cần model được fine-tune theo nghiệp vụ:

### 4.1 Model catalog

| Model | Base | Fine-tune data | Dùng cho |
|-------|------|----------------|----------|
| `hdtv-planner-v1` | Qwen 2.5 7B | 50K execution plans từ audit logs | PLANNER role |
| `hdtv-legal-v1` | Qwen 2.5 14B | Bộ luật VN, nghị định, thông tư EVN | LEGAL role |
| `hdtv-financial-v1` | Qwen 2.5 14B | Báo cáo tài chính, chuẩn mực kế toán | FINANCIAL role |
| `hdtv-critic-v1` | Qwen 2.5 72B | 100K cặp (báo cáo thô, báo cáo đã sửa) | CRITIC role |
| `hdtv-ocr-v1` | Qwen2-VL 7B | PDF scan EVN nội bộ | OCR role |

### 4.2 Training pipeline

```
Audit Logs (ai_audit_logs)
        ↓
Data Extraction & Cleaning
        ↓
RLHF / SFT Training (internal GPU cluster)
        ↓
Evaluation (benchmark vs general model)
        ↓
Deploy to vLLM cluster
        ↓
LLM Router cập nhật model mapping
```

**Feedback Loop:** Mỗi lần user submit feedback → data point mới cho fine-tuning cycle tiếp theo. Hệ thống tự cải thiện theo thời gian.

---

## 5. Multi-tenant Architecture

```
                    API Gateway (Kong)
                          ↓
                   Tenant Identification
                 (JWT claim: tenant_id)
                          ↓
            ┌─────────────┴─────────────┐
            ↓                           ↓
    Tenant EVN_SOUTH              Tenant EVN_NORTH
    ┌────────────────────┐        ┌────────────────────┐
    │ Schema: evn_south  │        │ Schema: evn_north  │
    │ Chroma NS: south   │        │ Chroma NS: north   │
    │ MinIO bucket:south │        │ MinIO bucket:north │
    │ Grafana org: south │        │ Grafana org: north │
    │ API Keys: isolated │        │ API Keys: isolated │
    └────────────────────┘        └────────────────────┘
```

**Data isolation levels:**
- **Database:** Schema-per-tenant trong PostgreSQL (hoặc database riêng cho tier cao)
- **Vector DB:** Chroma namespace per tenant
- **Object Storage:** MinIO bucket per tenant với bucket policy riêng
- **Observability:** Grafana organization per tenant (họ chỉ thấy data của mình)
- **API Keys:** Scoped per tenant, không thể cross-tenant access

---

## 6. Kubernetes Migration Path

Vì đã dùng Docker Compose với service definitions chuẩn, migration lên K8s là **lift-and-shift với minimal change**:

```yaml
# Từ docker-compose service:
services:
  hdtv-api:
    image: hdtv-api:latest
    environment:
      DATABASE_URL: ...

# Sang K8s Deployment:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hdtv-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: hdtv-api
        image: hdtv-api:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef: ...
```

**Không cần viết lại application code.** Chỉ cần:
1. Convert docker-compose → K8s manifests (có tool tự động: Kompose)
2. Thêm HPA (Horizontal Pod Autoscaler) cho FastAPI và Celery Worker
3. Thêm PVC (Persistent Volume Claim) thay volumes
4. Setup Ingress Controller (thay Traefik standalone)

---

## 7. SLA targets ở Enterprise Scale

| SLA Metric | Giai đoạn 2 | Giai đoạn 3 |
|------------|------------|------------|
| API availability | 99.5% | **99.9%** (≤ 8.7h downtime/năm) |
| Appraisal P95 latency | < 60s | < 30s |
| MTTR | < 4h | **< 1h** |
| Data backup RPO | 24h | **1h** (continuous replication) |
| Data backup RTO | 4h | **15 phút** |
| Concurrent appraisals | 12 | **100+** |
