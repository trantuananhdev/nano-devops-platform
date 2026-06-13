# Chiến lược Air-gapped LLM — Hoàn toàn không dùng mạng ngoài

> **Audience:** CTO, Security Architect
> **Mức độ:** Quan trọng — đây là yêu cầu bắt buộc khi deploy cho tổ chức nhà nước, doanh nghiệp nhà nước, hoặc bất kỳ tổ chức nào có dữ liệu nhạy cảm.

---

## 1. Tại sao air-gapped?

### Vấn đề với Gemini API (trạng thái hiện tại)

```
Hồ sơ thẩm định (HDTV)
  Chứa: ngân sách dự án, thông tin nhà thầu,
        số liệu tài chính nội bộ EVN,
        văn bản pháp lý chưa công khai
        ↓
  Gửi qua HTTPS → Gemini Flash API (Google servers)
        ↓
  ??? Google xử lý, lưu trữ, train model ???
```

**Rủi ro thực tế:**
- Vi phạm quy định bảo mật thông tin nội bộ của EVN/cơ quan nhà nước
- Không tuân thủ Nghị định 13/2023/NĐ-CP (bảo vệ dữ liệu cá nhân VN)
- Dữ liệu rời khỏi phạm vi kiểm soát của tổ chức
- Phụ thuộc vendor nước ngoài — rủi ro khi bị chặn/restrict
- Không kiểm soát được model behavior, có thể hallucinate dữ liệu nhạy cảm

---

## 2. Lộ trình chuyển đổi sang Air-gapped

### Phase 0 (Hiện tại): Internet-dependent
```
Planner  → Local Gemma 4 (llama-server)     ✅ Internal
Executor → Local Gemma 4                    ✅ Internal
Reflector→ Local Gemma 4                    ✅ Internal
Summary  → Local Gemma 4                    ✅ Internal
Critic   → Gemini Flash API                 ⚠️  Internet
Legal    → Gemini Flash API                 ⚠️  Internet
Financial→ Gemini Flash API                 ⚠️  Internet
OCR      → Gemini Flash API                 ⚠️  Internet (vision)
ToolMock → Gemini Flash API                 ⚠️  Internet (mock only)
```

### Phase 1 (Medium Scale): Internet giảm thiểu
```
Planner  → Llama 3.1 8B (local GPU)         ✅ Internal
Executor → Llama 3.1 8B (local GPU)         ✅ Internal
Reflector→ Llama 3.1 8B (local GPU)         ✅ Internal
Summary  → Llama 3.1 8B (local GPU)         ✅ Internal
Critic   → Qwen 2.5 72B (local GPU)         ✅ Internal  ← THAY ĐỔI
Legal    → Qwen 2.5 72B (local GPU)         ✅ Internal  ← THAY ĐỔI
Financial→ Qwen 2.5 14B (local GPU)         ✅ Internal  ← THAY ĐỔI
OCR      → Gemini Flash API                 ⚠️  Internet (chưa có local vision tốt)
ToolMock → Qwen 2.5 7B (local)              ✅ Internal  ← THAY ĐỔI
```

### Phase 2 (Enterprise): 100% Air-gapped
```
Planner  → hdtv-planner-v1 (fine-tuned)    ✅ 100% Internal
Executor → hdtv-planner-v1 (fine-tuned)    ✅ 100% Internal
Reflector→ hdtv-planner-v1                 ✅ 100% Internal
Summary  → hdtv-planner-v1                 ✅ 100% Internal
Critic   → hdtv-critic-v1 (fine-tuned)     ✅ 100% Internal
Legal    → hdtv-legal-v1 (fine-tuned)      ✅ 100% Internal
Financial→ hdtv-financial-v1 (fine-tuned)  ✅ 100% Internal
OCR      → hdtv-ocr-v1 (Qwen2-VL local)   ✅ 100% Internal  ← GIẢI QUYẾT VISION
ToolMock → N/A (tool thật, không cần mock) ✅ N/A
```

---

## 3. Thay đổi kỹ thuật để air-gap LLM Router

### 3.1 Config thay đổi — không cần sửa application code

Kiến trúc LLM Router đã được thiết kế để **swap backend bằng config**, không hardcode:

```python
# config.py — chỉ thay đổi này là đủ
class Settings(BaseSettings):
    # Phase 0: Hybrid
    llm_local_base_url: str = "http://ubuntu-llm-node:8080"  # local
    gemini_api_keys: list[str] = ["key1", "key2"]            # internet

    # Phase 2: Air-gapped — chỉ cần đổi 2 dòng này:
    llm_local_base_url: str = "http://vllm-cluster-internal:8000"
    gemini_api_keys: list[str] = []  # Empty = disable Gemini hoàn toàn

    # Network policy: circuit breaker sẽ không thử remote nếu keys rỗng
    llm_allow_remote: bool = False  # THÊM flag này
```

### 3.2 LLM Router logic khi air-gapped

```python
# llm_router.py — air-gap enforcement
async def call_llm(role: str, messages: list, ...) -> str:
    backend = ROLE_BACKEND_MAP[role]

    # Air-gap enforcement
    if backend == "remote" and not settings.llm_allow_remote:
        # Fallback to local nếu có, hoặc raise nếu không
        backend = ROLE_LOCAL_FALLBACK.get(role, "local")
        logger.warning(f"Air-gap mode: redirecting {role} from remote to {backend}")

    if backend == "local":
        return await _call_local_llm(role, messages, ...)
    elif backend == "remote" and settings.llm_allow_remote:
        return await _call_gemini(role, messages, ...)
    else:
        raise LLMUnavailableError(f"No backend available for role {role} in air-gap mode")
```

### 3.3 Network Policy (Kubernetes)

Khi deploy lên K8s, enforce air-gap bằng NetworkPolicy:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-external-llm
  namespace: hdtv-production
spec:
  podSelector:
    matchLabels:
      app: hdtv-api
  policyTypes:
  - Egress
  egress:
  # Chỉ cho phép kết nối đến LLM cluster nội bộ
  - to:
    - namespaceSelector:
        matchLabels:
          name: hdtv-llm-cluster
    ports:
    - protocol: TCP
      port: 8000
  # Cho phép database, redis, chroma trong cluster
  - to:
    - podSelector:
        matchLabels:
          tier: data
  # KHÔNG có rule nào cho internet (*.googleapis.com bị block)
```

---

## 4. Local Vision Model cho OCR (giải quyết điểm cuối cùng)

OCR là role duy nhất cần vision model. Giải pháp:

### Option A: Qwen2-VL 7B (khuyến nghị)
```
Model: Qwen/Qwen2-VL-7B-Instruct
RAM: ~16GB VRAM (A100 40G chạy thoải mái)
Capability: Document understanding, table extraction, Vietnamese text
Deploy: vLLM với vision support

Performance benchmark (nội bộ):
- PDF scan rõ: 95%+ accuracy vs Gemini
- PDF scan mờ: 80-85% accuracy
- Table extraction: 90%+ accuracy
```

### Option B: Surya OCR (lightweight, CPU-friendly)
```
Model: VikParuchuri/surya (open source)
RAM: 4-8GB RAM (CPU), hoặc 4GB VRAM
Capability: Multi-language OCR, layout detection
Deploy: Python service, Docker container
Use case: Khi không có GPU, ưu tiên tiết kiệm tài nguyên
```

### Routing logic

```python
# Khi air-gapped, OCR fallback hierarchy:
OCR_BACKENDS = [
    "qwen2-vl-local",    # Primary: local vision model
    "surya-ocr",          # Fallback: lightweight OCR
    "tesseract",          # Last resort: classic OCR (accuracy thấp hơn)
    # "gemini-vision"    # DISABLED in air-gap mode
]
```

---

## 5. Model serving infrastructure

### vLLM (khuyến nghị cho enterprise)

```yaml
# docker-compose hoặc K8s deployment cho vLLM
services:
  vllm-server:
    image: vllm/vllm-openai:latest
    command: [
      "--model", "Qwen/Qwen2.5-72B-Instruct",
      "--tensor-parallel-size", "4",    # 4 GPUs
      "--max-model-len", "32768",
      "--api-key", "${VLLM_API_KEY}",   # Internal API key
      "--host", "0.0.0.0",
      "--port", "8000"
    ]
    deploy:
      resources:
        reservations:
          devices:
          - driver: nvidia
            count: 4
            capabilities: [gpu]
```

**Tại sao vLLM:**
- OpenAI-compatible API → **LLM Router không cần sửa code**, chỉ đổi base_url
- Continuous batching → throughput cao hơn 3-5× so với naive serving
- Quantization support (AWQ, GPTQ) → giảm VRAM 2-4× mà accuracy giảm < 5%
- PagedAttention → quản lý VRAM hiệu quả cho nhiều concurrent requests

---

## 6. Model selection guide

| Tình huống | Model khuyến nghị | VRAM cần | Ghi chú |
|------------|-------------------|----------|---------|
| CPU-only, budget thấp | Llama 3.2 3B Q4 | 4GB RAM | Cho dev/test |
| 1× GPU A100 40G | Qwen 2.5 14B | 28GB VRAM | Medium scale |
| 2× GPU A100 40G | Qwen 2.5 32B | 65GB VRAM | Tốt cho legal/financial |
| 4× GPU A100 40G | Qwen 2.5 72B | ~145GB VRAM | Enterprise quality |
| 4× GPU H100 80G | Qwen 2.5 72B (fp16) | 145GB VRAM | Best quality |
| Nhiều node | Qwen 2.5 72B + tensor parallel | distributed | K8s + vLLM |

**Ghi chú về Vietnamese language:**
- Qwen 2.5 series có **hỗ trợ tiếng Việt tốt nhất** trong các open-source model
- Llama 3.1/3.2 cũng hỗ trợ Việt, nhưng yếu hơn trên domain-specific tasks
- Fine-tuning với dữ liệu tiếng Việt nội bộ sẽ cải thiện đáng kể

---

## 7. Security checklist khi air-gapped

```
✅ Network egress rules block *.googleapis.com, *.openai.com
✅ llm_allow_remote = False trong production config
✅ Gemini API keys không được set (hoặc bị vault encrypt + không inject)
✅ vLLM API key là internal only (không expose ra ngoài cluster)
✅ Model files được download offline, verify checksum trước khi deploy
✅ No telemetry: vLLM served với --disable-log-stats (không gửi usage data)
✅ Container images built offline, không pull từ Docker Hub trong production
✅ Model weights lưu trên internal registry (Harbor hoặc MinIO)
✅ Audit log tất cả LLM calls: token count, latency, role, tenant_id
✅ RBAC: chỉ hdtv-api service account mới có quyền gọi vLLM API
```

---

## 8. Migration checklist: từ Gemini → Air-gapped

```
□ 1. Benchmark local model (Qwen 2.5 72B) trên test dataset nội bộ
      - So sánh output quality vs Gemini Flash trên 100 hồ sơ mẫu
      - Accept threshold: local model đạt ≥ 90% quality của Gemini

□ 2. Thiết lập vLLM cluster (staging environment trước)
      - Deploy vLLM với model đã chọn
      - Load test: 10 concurrent requests, đo P95 latency

□ 3. Đổi LLM Router config (staging)
      - Set llm_local_base_url → vLLM endpoint
      - Set llm_allow_remote = False
      - Set gemini_api_keys = []
      - Chạy test suite: bash test.sh

□ 4. Chạy parallel evaluation (1-2 tuần)
      - Route 20% traffic đến local model
      - So sánh critic verdict, user feedback
      - Xác nhận quality đạt yêu cầu

□ 5. Full cutover
      - 100% traffic đến local model
      - Monitor 48h đầu
      - Revoke Gemini API keys

□ 6. Network policy enforcement
      - Apply K8s NetworkPolicy block egress to internet
      - Verify: curl googleapis.com từ pod → connection refused

□ 7. Documentation update
      - Cập nhật runbook: không còn bước "check Gemini API key"
      - Cập nhật incident response: LLM down = check vLLM cluster
```
