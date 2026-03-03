==================================================
SOURCE_PATH: ./docs-ai-context/adr-template/index.md
==================================================
# ADR

## Context
## Decision
## Trade-offs
## Consequences


==================================================
SOURCE_PATH: ./docs-ai-context/ai-coding-guidelines.md
==================================================
# AI Coding Guidelines

These guidelines define how an AI agent (e.g. Cursor) should design and implement changes so they remain safe, efficient, and aligned with the **Platform Master Strategy**.

---

## 1. Core Principles

- **Constraint-driven design**
  - Always assume a **single-node VM with 6GB RAM**.
  - Prefer low-memory components and reuse existing shared infrastructure.
- **GitOps only**
  - All changes must be made through Git, not by editing files directly on the VM.
- **Immutable deployment**
  - Never patch a running container; always build and deploy a new image.
- **Observability-first**
  - Every new or changed service must have metrics and logs integrated into the platform stack.
- **Automation-first**
  - Prefer scripts and pipelines over manual commands; keep runbooks script-oriented.

---

## 2. When Adding a New Service

When adding a new application service, the AI must follow this high-level flow:

```text
Read docs
  ↓
Design service (API, dependencies, resource estimate)
  ↓
Update app code + service config
  ↓
Wire into CI (build & test)
  ↓
Wire into CD (deploy & rollback)
  ↓
Add observability (metrics, logs, dashboards)
  ↓
Update documentation
```

### 2.1 Required Steps

1. **Update application code and service definition**
   - Add a new service under the designated apps area (following existing patterns).
   - Add or update entries in the Docker Compose configuration for the **application layer only**.
2. **Update CI**
   - Ensure the CI pipeline builds and tests the new service.
   - Reuse existing stages (lint, build, test, package) where possible.
3. **Update CD**
   - Ensure the deployment scripts/pipelines can:
     - Deploy the new service,
     - Perform health checks,
     - Support rollback using previous images.
4. **Update monitoring**
   - Add Prometheus scrape configuration for the new service.
   - Ensure logs are collected by Loki.
   - Optionally add/update Grafana dashboards.
5. **Update documentation**
   - Document:
     - Service purpose and responsibilities,
     - Dependencies,
     - Resource expectations,
     - Runbook entries relevant to this service.

---

## 3. Resource Awareness and Limits

- **Hard limit**: The total platform must fit into **6GB RAM**.
- AI must:
  - Estimate the memory footprint of any new long-running service.
  - Prefer:
    - **Multi-process containers** (one container running multiple simple workers) over many small containers.
    - **Shared infrastructure** (single PostgreSQL, single logging/metrics stack) over per-service instances.
  - Avoid:
    - Per-service databases by default.
    - Heavy sidecars for functionality that already exists (e.g. per-service log shippers if Loki is present).
  - Refuse to add a service if a reasonable estimate shows the memory budget would be exceeded without removing or tuning something else.

If the resource impact is uncertain, the AI should:

- Propose a lightweight design,
- Clearly document assumptions and ask for human validation rather than forcing the change.

---

## 4. Safe Patterns vs. Unsafe Patterns

### 4.1 Prefer (Safe)

- Reusing **existing PostgreSQL** for additional schemas or tables when needed.
- Adding lightweight HTTP services behind the existing reverse proxy.
- Exporting basic metrics (request count, latency, error rate, resource usage).
- Batch or cron-style jobs that:
  - Run infrequently,
  - Shut down after completion,
  - Have bounded runtime and memory.

### 4.2 Avoid (Unsafe)

- Creating new always-on databases for each service.
- Adding large, memory-heavy components (e.g. full-text search clusters, distributed queues) without:
  - A clear capacity analysis,
  - An explicit architectural decision.
- Introducing new orchestration layers (Kubernetes, service mesh).
- Modifying core runtime infra (reverse proxy, shared DB, monitoring stack) without human review.

---

## 5. Example: Adding a Simple HTTP Service

This example shows the **expected behaviour** from an AI agent when adding a new service called `report-service`.

1. **Design**
   - Stateless HTTP API that reads from PostgreSQL and returns reports.
   - Estimate memory usage to be small (tens of MB).
2. **Code & config**
   - Create `/apps/report-service` with application code.
   - Add a `report-service` entry in the application Docker Compose file:
     - Connect to the existing PostgreSQL instance.
     - Expose metrics endpoint.
3. **CI**
   - Reuse existing jobs:
     - Add `report-service` build and test steps to CI configuration.
4. **CD**
   - Ensure CD scripts:
     - Can deploy `report-service` using rolling update with health checks.
     - Tag and use versioned images for rollback.
5. **Observability**
   - Add Prometheus scrape job for `report-service`.
   - Ensure logs are sent to Loki with clear labels.
6. **Docs**
   - Update:
     - Architecture docs to include `report-service`.
     - Any relevant runbook entries.
     - AI context if `report-service` becomes a common dependency.

---

## 6. AI Self-Check Before Submitting Changes

**CRITICAL**: See `ai-safety-workflow.md` for the complete workflow. You **MUST** log all actions and generate an execution summary. You **MUST NOT** perform Git operations (checkout, commit, push, merge).

Before finalizing a change, the AI should verify:

1. **Constraints**
   - Memory and CPU usage are consistent with `platform-constraints.md` and `runtime-environment.md`.
2. **Consistency with master strategy**
   - No introduction of disallowed technologies (Kubernetes, service mesh, heavy sidecars).
3. **Deployment safety**
   - Changes are deployable via existing or extended CI/CD pipelines.
   - Rollback path is clear (previous image version).
4. **Observability**
   - New code exposes basic metrics and logs.
5. **Documentation**
   - All relevant documents in `/docs` have been updated to reflect the change.
6. **Logging and verification** (see `ai-safety-workflow.md`)
   - All actions logged
   - Execution summary generated
   - Verification status reported (✅/⚠️/❌)

If any of these checks fail, the AI should **stop**, explain the conflict in the execution log, and request human guidance instead of forcing a design that violates the platform strategy.



==================================================
SOURCE_PATH: ./docs-ai-context/ai-platform-build-plan.md
==================================================
## AI Execution Plan — Nano DevOps Platform (with Odoo)

### 1. Mục tiêu & phạm vi

- **Mục tiêu chính**: dùng bộ tài liệu trong `@docs/ai-context` và `@docs/final_devops_context.md` để AI (Cursor) lần lượt:
  - Dựng một Nano DevOps Platform chạy được trên single-node 6GB RAM,
  - Tích hợp **Odoo** như sản phẩm thử nghiệm (demo app) trên platform,
  - Tối ưu và cập nhật lại toàn bộ docs để phản ánh kiến trúc “platform + Odoo”.
- **Đối tượng**: AI agent làm việc trong Cursor, tuân thủ:
  - `ai-context/cursor-system-promt.md`,
  - `ai-context/platform-laws.yaml`,
  - `ai-context/law-context-mapping.yaml`,
  - Các section tương ứng trong `final_devops_context.md`.

---

### 2. Các pha thực hiện (overview)

- **Pha 0 – Context & guardrail**
  - Đảm bảo AI luôn load đúng context, hiểu luật, và làm việc theo small batch / trunk-based.
- **Pha 1 – Skeleton platform & core infra**
  - Tạo cấu trúc repo, docker-compose cơ bản cho runtime & infra cốt lõi (Traefik, PostgreSQL, monitoring stack).
- **Pha 2 – CI/CD skeleton**
  - Thiết kế & implement pipeline CI/CD tối thiểu (lint → build → test → package → security & law checks) + script CD.
- **Pha 3 – Observability & SLO**
  - Cấu hình Prometheus, Grafana, Loki, SLI/SLO, alert cơ bản.
- **Pha 4 – Sample application service (đơn giản)**
  - Thêm 1 service demo nhẹ để validate CI/CD + observability end-to-end.
- **Pha 5 – Odoo integration**
  - Container hóa và tích hợp Odoo vào platform, kết nối PostgreSQL, CI/CD, observability.
- **Pha 6 – Docs & ADR hardening (Odoo-aware)**
  - Cập nhật kiến trúc, runbook, AI-context & ADR để Odoo trở thành sản phẩm mẫu chính thức.

Mọi pha đều phải tuân thủ:

- `delivery.small_batch.max_lines` (≈ ≤ 300 dòng thay đổi / batch),
- `delivery.trunk_based.max_branch_lifetime_hours` (branch sống < 24h),
- Luật về reliability, observability, security, infra trong `platform-laws.yaml`.

---

### 3. Pha 0 — Context & guardrail cho AI

**Mục tiêu**: Đảm bảo mỗi lần AI làm việc đều:

- Đọc đúng tài liệu nguồn (theo `cursor-system-promt.md`),
- Xác định section trong `final_devops_context.md` bị ảnh hưởng,
- Liệt kê luật áp dụng trước khi tạo patch.

**Prompt khung dùng cho mọi task (template)**:

```text
Hãy đọc theo thứ tự:
- @docs/ai-context/platform-vision.md
- @docs/ai-context/platform-laws.yaml
- @docs/ai-context/law-context-mapping.yaml
- @docs/ai-context/ai-safety-workflow.md (MANDATORY: defines your responsibilities)
- @docs/final_devops_context.md
- (các file domain-specific sẽ nêu ở dưới)

Nhiệm vụ cụ thể: [mô tả ngắn task, ví dụ: tạo skeleton docker-compose cho core infra].

LƯU Ý: Bạn chỉ được phép EXECUTE, LOG, và VERIFY. KHÔNG được checkout branch, commit, push, hoặc merge. Xem ai-safety-workflow.md để biết chi tiết.

1) Xác định:
   - final_devops_context section nào bị ảnh hưởng,
   - Các law nào trong platform-laws áp dụng (delivery, reliability, observability, security, infra).
2) Đề xuất plan thực thi ngắn gọn (3–5 bước) theo small batch (≤ ~300 lines).
3) Tự thực thi plan:
   - Tạo/chỉnh sửa file cần thiết,
   - LOG mọi hành động (theo format trong ai-safety-workflow.md),
   - Không vượt quá small batch,
   - Giải thích ngắn gọn vì sao patch tuân thủ luật.
4) Self-verify (theo ai-safety-workflow.md):
   - Constraint fit, GitOps compliance, immutable deployment, observability, documentation, small batch.
5) Generate execution summary (theo format trong ai-safety-workflow.md).
6) Nếu task đụng trade-off lớn (tài nguyên, kiến trúc), hãy tạo ADR theo @docs/ai-context/adr-template/index.md thay vì thực hiện im lặng.
```

---

### 4. Pha 1 — Skeleton platform & core infra

**Mục tiêu**:

- Cấu trúc repo & filesystem phù hợp:
  - Theo `docs/ai-context/code-generation-rules/repo-structure.yaml`,
  - Và `docs/04-environment-and-infrastructure/filesystem-layout.md`.
- Docker Compose skeleton cho:
  - Traefik (Edge),
  - PostgreSQL (Data),
  - Monitoring stack (Prometheus, Grafana, Loki),
  - (Chưa tích hợp Odoo ở pha này).

**Context cần load cho pha 1**:

- `@docs/ai-context/cursor-system-promt.md`
- `@docs/ai-context/platform-laws.yaml`
- `@docs/ai-context/law-context-mapping.yaml`
- `@docs/ai-context/code-generation-rules/repo-structure.yaml`
- `@docs/04-environment-and-infrastructure/filesystem-layout.md`
- `@docs/02-system-architecture/high-level-architecture.md`
- `@docs/03-tech-stack/tech-stack.md`

**Tasks chính**:

1. Tạo cấu trúc thư mục repo (apps, infra, scripts, v.v.).
2. Tạo `docker-compose.yml` hoặc bộ compose tương đương cho core infra.
3. Thêm stub config/thư mục cho monitoring, CI, CD (chưa chi tiết).

**Prompt gợi ý cho Task 1 (cấu trúc repo)**:

```text
Context:
- @docs/ai-context/platform-laws.yaml
- @docs/ai-context/code-generation-rules/repo-structure.yaml
- @docs/04-environment-and-infrastructure/filesystem-layout.md
- @docs/final_devops_context.md

Nhiệm vụ:
- Tạo cấu trúc thư mục repo và, nếu cần, file README/stub cho:
  - apps/
  - infra/
  - monitoring/
  - ci/
  - scripts/
  - ai-context/ (nếu cần mirror trên runtime)

Yêu cầu:
- Tuân thủ law về infra (immutable, idempotent, environment parity).
- Mỗi thay đổi không vượt quá ~300 dòng.
- Giải thích ngắn cách cấu trúc này map sang filesystem /opt/platform trong runtime.
```

**Prompt gợi ý cho Task 2 (docker-compose core infra)**:

```text
Context:
- @docs/02-system-architecture/high-level-architecture.md
- @docs/03-tech-stack/tech-stack.md
- @docs/04-environment-and-infrastructure/runtime-environment.md
- @docs/ai-context/platform-laws.yaml

Nhiệm vụ:
- Tạo một file docker-compose (hoặc tập file) cho core infra:
  - traefik (edge),
  - platform-postgres (database),
  - prometheus, grafana, loki (observability).

Yêu cầu:
- Tuân thủ 6GB RAM, tránh service mesh, tránh Kubernetes.
- Config tách khỏi image (dùng volume cho config/data, không hard-code secrets).
- Giữ patch nhỏ, và mô tả group service nào thuộc layer nào trong final_devops_context.
```

---

### 5. Pha 2 — CI/CD skeleton

**Mục tiêu**:

- CI pipeline với các stage:
  - Lint,
  - Build,
  - Test,
  - Package,
  - Security & law checks.
- Script CD triển khai docker-compose lên VM single-node, rolling update với health check.

**Context cần load**:

- `@docs/05-ci-cd/ci-architecture.md`
- `@docs/05-ci-cd/gitops-architecture.md`
- `@docs/05-ci-cd/cd-strategy.md`
- `@docs/ai-context/platform-laws.yaml`
- `@docs/ai-context/ci-enforcement/law-checks.yaml`

**Tasks chính**:

1. Chọn hệ CI mặc định (ví dụ: GitHub Actions hoặc GitLab CI) và tạo pipeline file skeleton.
2. Tạo script CD cơ bản (`scripts/deploy-platform.sh`, `scripts/rollback-platform.sh`).
3. Stub script cho security & law checks (chưa cần logic đầy đủ nhưng thể hiện hook).

**Prompt gợi ý cho Task 1 (CI pipeline)**:

```text
Context:
- @docs/05-ci-cd/ci-architecture.md
- @docs/05-ci-cd/gitops-architecture.md
- @docs/ai-context/platform-laws.yaml
- @docs/ai-context/ci-enforcement/law-checks.yaml

Nhiệm vụ:
- Tạo file pipeline CI skeleton (chọn một trong: GitHub Actions / GitLab CI).
- Bao gồm các stage: lint, build, test, package, security_and_law_checks.

Yêu cầu:
- Mỗi stage có lệnh giả (echo hoặc comment) để dễ lấp sau.
- Mô tả rõ cách stage security_and_law_checks sẽ:
  - chạy SAST,
  - dependency scan,
  - secret scan,
  - validate law-checks (small_batch, trunk_based, unit_test_present, slo_defined, telemetry_present).
- Giữ patch ≤ 300 dòng.
```

**Prompt gợi ý cho Task 2 (CD scripts)**:

```text
Context:
- @docs/05-ci-cd/cd-strategy.md
- @docs/06-deployment-strategy/deployment-pattern.md
- @docs/10-runbook/incident-response.md

Nhiệm vụ:
- Tạo script shell trong thư mục scripts/ để:
  - deploy toàn bộ platform (docker compose up với health check),
  - rollback về version trước (docker compose với image tag trước đó).

Yêu cầu:
- Script phải phù hợp immutable deployment (không patch container đang chạy).
- Có log tối thiểu và exit code rõ ràng.
- Đảm bảo tài nguyên 6GB không bị phá vỡ (ví dụ: không scale replica quá nhiều).
```

---

### 6. Pha 3 — Observability & SLO

**Mục tiêu**:

- Config tối thiểu cho:
  - Prometheus (scrape node, docker, core services),
  - Loki,
  - (Optionally) alert rules cho SLO chính.

**Context cần load**:

- `@docs/07-observability/monitoring-architecture.md`
- `@docs/07-observability/sli-slo-sla.md`
- `@docs/ai-context/platform-laws.yaml` (observability.telemetry_required)

**Tasks chính**:

1. Tạo file config Prometheus cơ bản (job cho infra + chỗ để thêm app).
2. Tạo cấu hình Loki và wiring log từ container.
3. Thêm một vài alert rule liên quan tới SLO (availability, error rate).

**Prompt gợi ý (Prometheus + SLO)**:

```text
Context:
- @docs/07-observability/monitoring-architecture.md
- @docs/07-observability/sli-slo-sla.md
- @docs/ai-context/platform-laws.yaml

Nhiệm vụ:
- Tạo config Prometheus tối thiểu:
  - job cho node/docker,
  - job cho core infra services (traefik, postgres, prometheus/grafana/loki).
- Thêm 1–2 alert rule basic theo SLO (availability, deployment success rate).

Yêu cầu:
- Giải thích cách config này đáp ứng telemetry_required (logs, metrics; traces được đánh dấu future như docs).
- Không vượt quá small batch.
```

---

### 7. Pha 4 — Sample application service (đơn giản)

**Mục tiêu**:

- Có ít nhất một service demo (ví dụ `sample-service`) để:
  - Thử CI/CD end-to-end,
  - Xuất logs + metrics,
  - Có health check + SLO cơ bản.

**Context cần load**:

- `@docs/ai-context/ai-coding-guidelines.md`
- `@docs/ai-context/golden-path/service.yaml`
- `@docs/02-system-architecture/data-flow.md`
- `@docs/11-development-guide/local-development.md`

**Tasks chính**:

1. Thiết kế `sample-service` (ngôn ngữ tùy chọn, nhưng nhẹ, phù hợp 6GB).
2. Tạo code + Dockerfile + entry trong docker-compose.
3. Hook vào CI (build/test) và monitoring (metrics/logs).
4. Update docs (system-architecture, local-development) để nhắc đến service này.

**Prompt gợi ý (service demo)**:

```text
Context:
- @docs/ai-context/ai-coding-guidelines.md
- @docs/ai-context/golden-path/service.yaml
- @docs/02-system-architecture/data-flow.md

Nhiệm vụ:
- Tạo service demo 'sample-service' (stateless HTTP API) với:
  - /health endpoint,
  - 1 endpoint business đơn giản (ví dụ /hello),
  - metrics Prometheus cơ bản (request count, latency, error count),
  - structured logs.

Yêu cầu:
- Service tuân thủ layering trong golden-path/service.yaml.
- Được add vào docker-compose và CI pipeline.
- Có test tối thiểu.
```

---

### 8. Pha 5 — Odoo integration

**Mục tiêu**:

- Chạy **Odoo** như một ứng dụng mẫu trên platform:
  - Reuse PostgreSQL hiện có (schema/DB riêng),
  - Được expose qua Traefik,
  - Có CI/CD cơ bản,
  - Có observability & SLO tối thiểu.

**Lưu ý về constraint**:

- Odoo khá nặng, cần đặc biệt chú ý:
  - Memory footprint trong 6GB RAM (xem `runtime-environment.md`),
  - Có thể cần ADR nếu resource usage quá lớn.

**Context cần load**:

- Toàn bộ context trước (Pha 1–4), cộng thêm:
  - `@docs/03-tech-stack/tech-stack-decision.md` (lý do chọn công nghệ),
  - `@docs/08-security/security-baseline.md`,
  - Bất kỳ tài liệu Odoo official (qua web_search nếu cần).

**Tasks chính**:

1. **Thiết kế kiến trúc tích hợp Odoo**:
   - Odoo app container,
   - Reuse `platform-postgres` với DB/schema riêng cho Odoo,
   - Expose qua Traefik với host/path riêng.
   - Đánh giá sơ bộ memory usage và tạo ADR nếu sát ngưỡng 6GB.
2. **Implement Odoo service**:
   - Docker image (dùng official image + minimal config),
   - docker-compose service,
   - environment configuration (DB conn, admin user).
3. **CI/CD cho Odoo**:
   - Job build/pull Odoo image (nếu cần custom),
   - Test sanity (healthcheck, basic HTTP check),
   - CD hook deploy/rollback Odoo.
4. **Observability & SLO cho Odoo**:
   - Logs gửi về Loki,
   - Metrics (if available) hoặc ít nhất exporter/side metrics,
   - Định nghĩa SLO basic cho web UI (availability, latency).

**Prompt gợi ý (thiết kế tích hợp Odoo + ADR)**:

```text
Context:
- @docs/ai-context/cursor-system-promt.md
- @docs/ai-context/platform-laws.yaml
- @docs/ai-context/law-context-mapping.yaml
- @docs/final_devops_context.md
- @docs/03-tech-stack/tech-stack-decision.md
- @docs/04-environment-and-infrastructure/runtime-environment.md

Nhiệm vụ:
- Đề xuất kiến trúc tích hợp Odoo vào Nano DevOps Platform:
  - Odoo container + kết nối tới platform-postgres,
  - Routing qua Traefik,
  - Ước lượng RAM/CPU để đảm bảo vẫn trong 6GB tổng.

Yêu cầu:
- Thực hiện STEP 1–2–3–4 trong cursor-system-promt (context, law validation, golden-path, architecture check).
- Nếu resource risk cao, hãy tạo ADR theo @docs/ai-context/adr-template/index.md để ghi rõ trade-off,
  trước khi implement chi tiết.
```

**Prompt gợi ý (implement Odoo service)**:

```text
Context:
- (ADR đã được chấp nhận nếu có)
- @docs/ai-context/ai-coding-guidelines.md
- @docs/02-system-architecture/high-level-architecture.md

Nhiệm vụ:
- Thêm service 'odoo' vào docker-compose:
  - Sử dụng image Odoo official (hoặc một biến thể nhẹ),
  - Kết nối tới PostgreSQL hiện có (DB/schema riêng),
  - Expose qua Traefik.
- Cập nhật CI/CD để:
  - build/pull image đúng version,
  - kiểm tra health endpoint của Odoo sau deploy.

Yêu cầu:
- Tuân thủ small batch (chia thành nhiều patch nếu cần).
- Mô tả rõ Odoo thuộc layer nào trong kiến trúc (Application Layer).
```

---

### 9. Pha 6 — Docs & ADR hardening (Odoo-aware)

**Mục tiêu**:

- Toàn bộ hệ thống docs phản ánh việc:
  - Odoo là sản phẩm mẫu chính,
  - Platform có thể demo năng lực DevOps/Platform/SRE thông qua Odoo.

**Context cần load**:

- `@docs/final_devops_context.md`
- `@docs/02-system-architecture/*`
- `@docs/03-tech-stack/*`
- `@docs/10-runbook/incident-response.md`
- `@docs/11-development-guide/*`
- `@docs/ai-context/*`

**Tasks chính**:

1. Cập nhật `system-overview`, `high-level-architecture`, `logical-architecture` để thể hiện Odoo là một ứng dụng chạy trên platform.
2. Cập nhật `tech-stack` để nhắc tới Odoo (như “sample business app”).
3. Cập nhật `local-development` & `contribution-guide` để hướng dẫn:
   - Chạy platform + Odoo locally,
   - Quy tắc thay đổi liên quan tới Odoo.
4. Cập nhật `ai-coding-guidelines.md` & `system-context.md` (nếu cần) để:
   - Cho phép AI hiểu Odoo là một dịch vụ ứng dụng,
   - Biết giới hạn thay đổi (không phá core runtime, không vượt budget).

**Prompt gợi ý (refactor docs sau Odoo)**:

```text
Context:
- @docs/final_devops_context.md
- @docs/02-system-architecture/high-level-architecture.md
- @docs/02-system-architecture/logical-architecture.md
- @docs/03-tech-stack/tech-stack.md
- @docs/11-development-guide/local-development.md

Nhiệm vụ:
- Cập nhật docs để:
  - Thêm Odoo vào các diagram/flow chính như một ứng dụng mẫu,
  - Giải thích ngắn use-case: dùng Odoo để chứng minh năng lực platform.

Yêu cầu:
- Không thay đổi constraint cốt lõi (single-node, 6GB).
- Thay đổi theo small batch, và mỗi patch phải nêu rõ law nào đang được giữ/được kiểm tra.
```

---

### 10. Cách sử dụng file kế hoạch này

**IMPORTANT**: Đọc `ai-safety-workflow.md` trước khi bắt đầu. Workflow này đảm bảo AI chỉ execute/log/verify, còn bạn quyết định Git operations.

- **Khi bắt đầu một batch công việc mới**:
  1. **Bạn**: Chọn **pha** + **task** trong file này
  2. **Bạn**: Tạo feature branch:
     ```bash
     git checkout -b feat/phase1-task1
     ```
  3. **Bạn**: Copy prompt gợi ý tương ứng vào Cursor, thêm note về ai-safety-workflow.md
  4. **AI**: Tự động thực thi (tạo/chỉnh file), log actions, self-verify, generate summary
  5. **Bạn**: Review execution log và git diff
  6. **Bạn**: Commit và merge (nếu approved):
     ```bash
     git add .
     git commit -m "feat: [task description]"
     git push origin feat/phase1-task1
     # Create PR, review, merge
     ```
- **Khi close một pha**:
  - Đảm bảo:
    - Docs trong `final_devops_context.md` vẫn còn đúng,
    - Không có vi phạm rõ ràng với `platform-laws.yaml`,
    - Nếu có trade-off lớn, đã có ADR trong `ai-context/adr-template/`,
    - Tất cả execution logs đã được review.

File này là **roadmap sống**: có thể (và nên) được cập nhật khi platform tiến hóa, nhưng mọi chỉnh sửa cũng phải tuân thủ cùng luật small batch / trunk-based như phần còn lại của dự án.




==================================================
SOURCE_PATH: ./docs-ai-context/ai-safety-workflow.md
==================================================
# AI Safety Workflow

This document defines the **safety workflow** for AI-assisted development on the Nano DevOps Platform. It ensures that AI-generated changes are **logged, verified, and reviewed** before affecting production, while clearly separating **AI responsibilities** from **human decision-making**.

---

## 1. Core Safety Principles

- **AI executes, humans decide**: AI performs tasks, logs actions, and verifies results. Humans control Git operations (branching, merging, deployment).
- **Nothing touches production without review**: All changes go through a reviewable branch and explicit human approval.
- **Full audit trail**: Every AI action must be logged and traceable.
- **Fail-safe defaults**: If verification fails, AI must stop and report, not proceed.

---

## 2. Workflow Overview

```text
Human: Select task from ai-platform-build-plan.md
  ↓
Human: Create feature branch (e.g., feat/phase1-task1)
  ↓
AI: Read context (platform-laws, final_devops_context, etc.)
  ↓
AI: Execute task (create/modify files)
  ↓
AI: Log all actions (what was changed, why, which laws applied)
  ↓
AI: Self-verify (constraints, laws, small batch)
  ↓
AI: Generate summary report
  ↓
Human: Review changes (diff, logs, summary)
  ↓
Human: Run local tests (if applicable)
  ↓
Human: Merge to main (if approved)
  ↓
CI/CD: Automated validation & deployment
```

---

## 3. AI Responsibilities (What AI Must Do)

### 3.1 Before Starting Any Task

AI **must**:

1. **Load required context** (in order):
   - `ai-context/platform-vision.md`
   - `ai-context/platform-laws.yaml`
   - `ai-context/law-context-mapping.yaml`
   - `final_devops_context.md` (relevant sections)
   - Domain-specific docs as needed

2. **Identify affected sections**:
   - Which `final_devops_context` section(s) are impacted
   - Which platform laws apply (delivery, reliability, observability, security, infra)

3. **Propose execution plan** (3–5 steps, ≤ 300 lines total):
   - List files to create/modify
   - Explain why each change is needed
   - Confirm small batch compliance

### 3.2 During Execution

AI **must**:

1. **Execute changes**:
   - Create/modify files as planned
   - Follow golden-path templates when applicable
   - Respect platform laws and constraints

2. **Log every action**:
   - What file was created/modified
   - What content was added/changed (brief summary)
   - Which platform law(s) this change enforces
   - Estimated resource impact (if applicable)

3. **Self-verify before completion**:
   - ✅ Constraint fit (6GB RAM, single-node)
   - ✅ GitOps compliance (all changes in Git, no manual-only steps)
   - ✅ Immutable deployment (no runtime patching)
   - ✅ Observability coverage (metrics/logs if new service)
   - ✅ Documentation updated (if needed)
   - ✅ Small batch (≤ 300 lines changed)

### 3.3 After Execution

AI **must**:

1. **Generate execution summary**:
   - List all files changed (with paths)
   - Summary of changes (what was done)
   - Laws applied and verified
   - Resource impact assessment (if applicable)
   - Any warnings or trade-offs

2. **Report verification status**:
   - ✅ All checks passed, or
   - ⚠️ Warnings (non-blocking), or
   - ❌ Blocking issues (must stop)

3. **Never**:
   - Checkout branches
   - Commit changes
   - Push to remote
   - Merge branches
   - Deploy to production

---

## 4. Human Responsibilities (What Humans Must Do)

### 4.1 Before AI Execution

Human **must**:

1. **Select task** from `ai-platform-build-plan.md`
2. **Create feature branch**:
   ```bash
   git checkout -b feat/phase1-task1
   ```
3. **Provide clear prompt** to AI:
   - Reference the task from build plan
   - Specify any additional context or constraints
   - Confirm AI should proceed

### 4.2 After AI Execution

Human **must**:

1. **Review AI-generated summary**:
   - Check execution log
   - Verify files changed match expectations
   - Confirm laws were applied correctly

2. **Inspect changes**:
   ```bash
   git status
   git diff
   ```
   - Review file-by-file changes
   - Verify no unintended modifications
   - Check for hardcoded secrets, resource violations, etc.

3. **Run local verification** (if applicable):
   - Lint/format checks
   - Local tests
   - Docker Compose validation (if infra changes)

4. **Decide on merge**:
   - ✅ **Approve**: Commit and prepare for merge
   - ⚠️ **Request changes**: Ask AI to fix issues
   - ❌ **Reject**: Discard branch, start over

5. **Commit and merge** (if approved):
   ```bash
   git add .
   git commit -m "feat: [task description]"
   git push origin feat/phase1-task1
   # Create PR, review, merge to main
   ```

---

## 5. Execution Log Format

AI must generate a log in this format for every task:

```markdown
## AI Execution Log

**Task**: [Task name from build plan]
**Branch**: [Current branch name - AI reads from git, does not create]
**Timestamp**: [ISO 8601 format]

### Context Loaded
- ✅ ai-context/platform-vision.md
- ✅ ai-context/platform-laws.yaml
- ✅ final_devops_context.md (sections: [list])

### Laws Applied
- delivery.small_batch (max_lines: 300)
- [other applicable laws]

### Execution Plan
1. [Step 1]
2. [Step 2]
...

### Files Changed
- `path/to/file1`: Created/Modified - [brief description]
- `path/to/file2`: Modified - [brief description]

### Verification Results
- ✅ Constraint fit: [explanation]
- ✅ GitOps compliance: [explanation]
- ✅ Immutable deployment: [explanation]
- ✅ Observability: [explanation if applicable]
- ✅ Small batch: [X lines changed, ≤ 300]

### Resource Impact
- Memory: [estimate if applicable]
- CPU: [estimate if applicable]

### Warnings
- [Any non-blocking warnings]

### Blocking Issues
- [Any issues that prevent merge - if none, state "None"]

### Summary
[2-3 sentence summary of what was done and why it's safe]
```

---

## 6. Safety Checks (AI Must Verify)

Before reporting completion, AI must verify:

### 6.1 Constraint Compliance
- ✅ Total memory impact ≤ 6GB (if adding services)
- ✅ No Kubernetes/service mesh introduced
- ✅ No per-service databases (unless justified)
- ✅ Single-node compatible

### 6.2 Law Compliance
- ✅ Small batch (≤ 300 lines changed)
- ✅ Trunk-based (branch lifetime < 24h - human responsibility, but AI notes)
- ✅ Unit tests present (if code changes)
- ✅ SLO/telemetry configured (if new service)
- ✅ Security scans pass (if CI changes)

### 6.3 GitOps Compliance
- ✅ All changes represented in Git
- ✅ No manual-only configuration paths
- ✅ No direct VM edits suggested
- ✅ Rollback path exists (previous image version)

### 6.4 Documentation
- ✅ Relevant docs updated (if behavior changes)
- ✅ Architecture diagrams updated (if structure changes)
- ✅ Runbooks updated (if operational changes)

---

## 7. Failure Modes and Responses

### 7.1 AI Detects Blocking Issue

**AI must**:
- Stop execution immediately
- Report the issue in execution log
- Explain why it's blocking
- Suggest remediation (if possible)

**Human must**:
- Review the blocking issue
- Decide: fix, workaround, or abandon task

### 7.2 Verification Fails

**AI must**:
- Report which check(s) failed
- Explain impact
- Suggest fixes

**Human must**:
- Review failures
- Request AI to fix, or fix manually
- Re-run verification

### 7.3 Resource Budget Exceeded

**AI must**:
- Stop before creating resource-heavy components
- Report estimated usage vs. budget
- Suggest alternatives or ADR

**Human must**:
- Review resource analysis
- Approve constraint change (via ADR), or request redesign

---

## 8. Integration with CI/CD

After human merges to `main`:

1. **CI pipeline runs**:
   - Lint, build, test, package
   - Security & law checks
   - If any stage fails → human must fix

2. **CD pipeline runs** (if CI passes):
   - Deploy to single-node VM
   - Health checks
   - Rollback if health checks fail

3. **AI is not involved** in CI/CD execution (automated)

---

## 9. Example: Complete Workflow

### Step 1: Human Creates Branch
```bash
git checkout -b feat/phase1-task1-skeleton-repo
```

### Step 2: Human Provides Prompt
```
Execute Phase 1 - Task 1 from ai-platform-build-plan.md:
- Create repo skeleton (apps/, infra/, scripts/, etc.)
- Follow repo-structure.yaml and filesystem-layout.md
- Keep changes ≤ 300 lines
- Generate execution log
```

### Step 3: AI Executes
- Loads context
- Creates directories and stub files
- Generates execution log
- Self-verifies
- Reports completion

### Step 4: Human Reviews
```bash
git status
git diff
# Review execution log
# Verify no violations
```

### Step 5: Human Commits (if approved)
```bash
git add .
git commit -m "feat: init platform skeleton (phase1-task1)"
git push origin feat/phase1-task1-skeleton-repo
```

### Step 6: Human Creates PR
- Review PR diff
- CI runs automatically
- Merge if CI passes

### Step 7: CD Deploys (automated)
- CD pipeline runs
- Deploys to VM
- Health checks verify

---

## 10. Best Practices

### For Humans
- **Always review execution log** before committing
- **Test locally** before merging (if applicable)
- **Keep branches short-lived** (< 24h per platform laws)
- **One task per branch** (small batch principle)

### For AI
- **Never skip verification steps**
- **Always log actions** (even if trivial)
- **Report warnings** (don't hide issues)
- **Stop on blocking issues** (don't proceed hoping human will catch it)

---

## 11. Emergency Procedures

### If AI Makes Unintended Changes

1. **Human stops AI** (if still running)
2. **Review git diff**:
   ```bash
   git diff
   git status
   ```
3. **Discard unwanted changes**:
   ```bash
   git checkout -- <file>
   # or
   git reset --hard HEAD
   ```
4. **Restart task** with clearer prompt

### If Changes Are Merged but Cause Issues

1. **Rollback via GitOps**:
   ```bash
   git revert <commit-hash>
   git push
   ```
2. **CD automatically redeploys** previous version
3. **Investigate** root cause (was it AI error or missing context?)

---

## 12. Continuous Improvement

- **After each task**: Review execution log quality
- **After each phase**: Assess if workflow needs adjustment
- **Update this workflow** if patterns emerge (via PR, following same workflow)

---

This workflow ensures that **AI assists safely** while **humans maintain control** over all Git operations and production deployments.



==================================================
SOURCE_PATH: ./docs-ai-context/ci-enforcement/law-checks.yaml
==================================================
checks:

  - name: slo_defined
  - name: telemetry_present
  - name: unit_test_present
  - name: small_batch
  - name: trunk_based


==================================================
SOURCE_PATH: ./docs-ai-context/code-generation-rules/repo-structure.yaml
==================================================
when_create_repo:

  create:
    - apps/
    - platform/
    - infra/
    - ai-context/


==================================================
SOURCE_PATH: ./docs-ai-context/code-generation-rules/service-scaffold.yaml
==================================================
when_create_service:

  use_golden_path: service.yaml

  auto_generate:
    - healthcheck
    - telemetry
    - slo_config
    - test_structure


==================================================
SOURCE_PATH: ./docs-ai-context/cursor-system-promt.md
==================================================
# CURSOR SYSTEM PROMPT — PLATFORM ENGINEERING MODE

## 1. ROLE

You are not a generic coding assistant.

You are:

* a Platform Engineer
* a DevOps architect
* an SRE-aware system designer

Your job is to:

* build and refactor the system according to PLATFORM LAWS
* enforce architectural consistency
* optimize for delivery performance and reliability

You must NEVER generate code that violates platform laws.

---

## 2. SOURCE OF TRUTH (MANDATORY READING ORDER)

Before any action, you MUST read in this exact order:

1. ai-context/platform-vision.md
2. ai-context/platform-laws.yaml
3. ai-context/law-context-mapping.yaml

Then load:

4. golden-path/*
5. decision-trees/*
6. slo/*
7. code-generation-rules/*

For detailed guidelines and context:

8. ai-context/system-context.md
9. ai-context/ai-coding-guidelines.md
10. ai-context/ai-platform-build-plan.md (when planning major changes)
11. ai-context/ai-safety-workflow.md (MANDATORY: defines execution, logging, verification responsibilities)

If context is missing → STOP and ask.

---

## 3. GENERATION WORKFLOW

**CRITICAL**: You are an **executor and verifier**, NOT a Git operator. You **MUST NOT** checkout branches, commit, push, or merge. See `ai-safety-workflow.md` for full details.

For every request:

### STEP 1 — CONTEXT RESOLUTION

Identify:

* which final_devops_context section is affected
* which laws apply

### STEP 2 — LAW VALIDATION

Check:

* Is the change allowed by platform laws?
* Does it break DORA / SRE targets?
* Does it increase cognitive load?

If violation → propose compliant alternative.

### STEP 3 — GOLDEN PATH EXECUTION

If creating:

* service → use golden-path/service.yaml
* pipeline → use golden-path/pipeline.yaml
* environment → use golden-path/environment.yaml

Never invent structure.

### STEP 4 — ARCHITECTURE CHECK

All code must follow:

* stateless services
* explicit data flow
* clean architecture layering
* testability

### STEP 5 — EXECUTION & LOGGING (MANDATORY)

After making changes:

1. **Log every action**:
   - What files were created/modified
   - What content was changed (brief summary)
   - Which platform laws were applied
   - Resource impact (if applicable)

2. **Self-verify**:
   - ✅ Constraint fit (6GB RAM, single-node)
   - ✅ GitOps compliance (all changes in Git)
   - ✅ Immutable deployment (no runtime patching)
   - ✅ Observability coverage (if new service)
   - ✅ Documentation updated (if needed)
   - ✅ Small batch (≤ 300 lines changed)

3. **Generate execution summary**:
   - List all files changed
   - Summary of changes
   - Laws applied and verified
   - Verification status (✅/⚠️/❌)
   - Any warnings or blocking issues

4. **Never**:
   - Checkout branches
   - Commit changes
   - Push to remote
   - Merge branches
   - Deploy to production

See `ai-safety-workflow.md` for the complete execution log format.

---

## 4. DELIVERY PERFORMANCE OPTIMIZATION

Always optimize for:

* small batch changes
* trunk-based development
* fast feedback loops
* deployability

Reject designs that:

* require big-bang integration
* create long-lived branches
* hide integration risk

---

## 5. SRE & RELIABILITY MODE

Every runtime component MUST include:

* health check
* telemetry (logs, metrics, traces)
* SLO definition

If missing → auto-generate.

Apply error budget policy to release decisions.

---

## 6. OBSERVABILITY-FIRST DEVELOPMENT

Features are NOT complete until:

* measurable via SLIs
* observable in runtime

---

## 7. SECURITY BY DEFAULT

All pipelines MUST include:

* SAST
* dependency scan
* secret detection

Never generate insecure defaults.

---

## 8. INFRASTRUCTURE RULES

Infrastructure must be:

* immutable
* idempotent
* environment parity compliant

No manual mutation.

---

## 9. ADR REQUIREMENT

When a trade-off appears:

You MUST:

* generate an ADR
* explain:

  * context
  * decision
  * trade-offs
  * consequences

---

## 10. OUTPUT MODE

When generating:

### For code:

Explain:

* which laws are applied
* why the structure is chosen

### For refactoring:

Show:

* law violations detected
* compliant redesign

---

## 11. ANTI-GOALS

You must NOT:

* generate quick hacks
* optimize for local simplicity over system flow
* introduce hidden state
* bypass CI enforcement
* perform Git operations (checkout, commit, push, merge) — these are human responsibilities
* skip logging or verification steps
* proceed when verification fails (must stop and report)

---

## 12. SUCCESS CRITERIA

Your output increases:

* deployment frequency
* system reliability
* developer experience
* architectural consistency

If not → redesign.



==================================================
SOURCE_PATH: ./docs-ai-context/decision-trees/consistency.yaml
==================================================
rules:

  - condition: financial_transaction
    result: strong_consistency

  - condition: multi_region
    result: eventual_consistency


==================================================
SOURCE_PATH: ./docs-ai-context/decision-trees/scaling.yaml
==================================================
rules:

  - condition: read_heavy
    result: read_replica

  - condition: write_heavy
    result: sharding


==================================================
SOURCE_PATH: ./docs-ai-context/final_ai_context.md
==================================================
==================================================
SOURCE_PATH: ./docs-ai-context/adr-template/index.md
==================================================
# ADR

## Context
## Decision
## Trade-offs
## Consequences


==================================================
SOURCE_PATH: ./docs-ai-context/ai-coding-guidelines.md
==================================================
# AI Coding Guidelines

These guidelines define how an AI agent (e.g. Cursor) should design and implement changes so they remain safe, efficient, and aligned with the **Platform Master Strategy**.

---

## 1. Core Principles

- **Constraint-driven design**
  - Always assume a **single-node VM with 6GB RAM**.
  - Prefer low-memory components and reuse existing shared infrastructure.
- **GitOps only**
  - All changes must be made through Git, not by editing files directly on the VM.
- **Immutable deployment**
  - Never patch a running container; always build and deploy a new image.
- **Observability-first**
  - Every new or changed service must have metrics and logs integrated into the platform stack.
- **Automation-first**
  - Prefer scripts and pipelines over manual commands; keep runbooks script-oriented.

---

## 2. When Adding a New Service

When adding a new application service, the AI must follow this high-level flow:

```text
Read docs
  ↓
Design service (API, dependencies, resource estimate)
  ↓
Update app code + service config
  ↓
Wire into CI (build & test)
  ↓
Wire into CD (deploy & rollback)
  ↓
Add observability (metrics, logs, dashboards)
  ↓
Update documentation
```

### 2.1 Required Steps

1. **Update application code and service definition**
   - Add a new service under the designated apps area (following existing patterns).
   - Add or update entries in the Docker Compose configuration for the **application layer only**.
2. **Update CI**
   - Ensure the CI pipeline builds and tests the new service.
   - Reuse existing stages (lint, build, test, package) where possible.
3. **Update CD**
   - Ensure the deployment scripts/pipelines can:
     - Deploy the new service,
     - Perform health checks,
     - Support rollback using previous images.
4. **Update monitoring**
   - Add Prometheus scrape configuration for the new service.
   - Ensure logs are collected by Loki.
   - Optionally add/update Grafana dashboards.
5. **Update documentation**
   - Document:
     - Service purpose and responsibilities,
     - Dependencies,
     - Resource expectations,
     - Runbook entries relevant to this service.

---

## 3. Resource Awareness and Limits

- **Hard limit**: The total platform must fit into **6GB RAM**.
- AI must:
  - Estimate the memory footprint of any new long-running service.
  - Prefer:
    - **Multi-process containers** (one container running multiple simple workers) over many small containers.
    - **Shared infrastructure** (single PostgreSQL, single logging/metrics stack) over per-service instances.
  - Avoid:
    - Per-service databases by default.
    - Heavy sidecars for functionality that already exists (e.g. per-service log shippers if Loki is present).
  - Refuse to add a service if a reasonable estimate shows the memory budget would be exceeded without removing or tuning something else.

If the resource impact is uncertain, the AI should:

- Propose a lightweight design,
- Clearly document assumptions and ask for human validation rather than forcing the change.

---

## 4. Safe Patterns vs. Unsafe Patterns

### 4.1 Prefer (Safe)

- Reusing **existing PostgreSQL** for additional schemas or tables when needed.
- Adding lightweight HTTP services behind the existing reverse proxy.
- Exporting basic metrics (request count, latency, error rate, resource usage).
- Batch or cron-style jobs that:
  - Run infrequently,
  - Shut down after completion,
  - Have bounded runtime and memory.

### 4.2 Avoid (Unsafe)

- Creating new always-on databases for each service.
- Adding large, memory-heavy components (e.g. full-text search clusters, distributed queues) without:
  - A clear capacity analysis,
  - An explicit architectural decision.
- Introducing new orchestration layers (Kubernetes, service mesh).
- Modifying core runtime infra (reverse proxy, shared DB, monitoring stack) without human review.

---

## 5. Example: Adding a Simple HTTP Service

This example shows the **expected behaviour** from an AI agent when adding a new service called `report-service`.

1. **Design**
   - Stateless HTTP API that reads from PostgreSQL and returns reports.
   - Estimate memory usage to be small (tens of MB).
2. **Code & config**
   - Create `/apps/report-service` with application code.
   - Add a `report-service` entry in the application Docker Compose file:
     - Connect to the existing PostgreSQL instance.
     - Expose metrics endpoint.
3. **CI**
   - Reuse existing jobs:
     - Add `report-service` build and test steps to CI configuration.
4. **CD**
   - Ensure CD scripts:
     - Can deploy `report-service` using rolling update with health checks.
     - Tag and use versioned images for rollback.
5. **Observability**
   - Add Prometheus scrape job for `report-service`.
   - Ensure logs are sent to Loki with clear labels.
6. **Docs**
   - Update:
     - Architecture docs to include `report-service`.
     - Any relevant runbook entries.
     - AI context if `report-service` becomes a common dependency.

---

## 6. AI Self-Check Before Submitting Changes

**CRITICAL**: See `ai-safety-workflow.md` for the complete workflow. You **MUST** log all actions and generate an execution summary. You **MUST NOT** perform Git operations (checkout, commit, push, merge).

Before finalizing a change, the AI should verify:

1. **Constraints**
   - Memory and CPU usage are consistent with `platform-constraints.md` and `runtime-environment.md`.
2. **Consistency with master strategy**
   - No introduction of disallowed technologies (Kubernetes, service mesh, heavy sidecars).
3. **Deployment safety**
   - Changes are deployable via existing or extended CI/CD pipelines.
   - Rollback path is clear (previous image version).
4. **Observability**
   - New code exposes basic metrics and logs.
5. **Documentation**
   - All relevant documents in `/docs` have been updated to reflect the change.
6. **Logging and verification** (see `ai-safety-workflow.md`)
   - All actions logged
   - Execution summary generated
   - Verification status reported (✅/⚠️/❌)

If any of these checks fail, the AI should **stop**, explain the conflict in the execution log, and request human guidance instead of forcing a design that violates the platform strategy.



==================================================
SOURCE_PATH: ./docs-ai-context/ai-platform-build-plan.md
==================================================
## AI Execution Plan — Nano DevOps Platform (with Odoo)

### 1. Mục tiêu & phạm vi

- **Mục tiêu chính**: dùng bộ tài liệu trong `@docs/ai-context` và `@docs/final_devops_context.md` để AI (Cursor) lần lượt:
  - Dựng một Nano DevOps Platform chạy được trên single-node 6GB RAM,
  - Tích hợp **Odoo** như sản phẩm thử nghiệm (demo app) trên platform,
  - Tối ưu và cập nhật lại toàn bộ docs để phản ánh kiến trúc “platform + Odoo”.
- **Đối tượng**: AI agent làm việc trong Cursor, tuân thủ:
  - `ai-context/cursor-system-promt.md`,
  - `ai-context/platform-laws.yaml`,
  - `ai-context/law-context-mapping.yaml`,
  - Các section tương ứng trong `final_devops_context.md`.

---

### 2. Các pha thực hiện (overview)

- **Pha 0 – Context & guardrail**
  - Đảm bảo AI luôn load đúng context, hiểu luật, và làm việc theo small batch / trunk-based.
- **Pha 1 – Skeleton platform & core infra**
  - Tạo cấu trúc repo, docker-compose cơ bản cho runtime & infra cốt lõi (Traefik, PostgreSQL, monitoring stack).
- **Pha 2 – CI/CD skeleton**
  - Thiết kế & implement pipeline CI/CD tối thiểu (lint → build → test → package → security & law checks) + script CD.
- **Pha 3 – Observability & SLO**
  - Cấu hình Prometheus, Grafana, Loki, SLI/SLO, alert cơ bản.
- **Pha 4 – Sample application service (đơn giản)**
  - Thêm 1 service demo nhẹ để validate CI/CD + observability end-to-end.
- **Pha 5 – Odoo integration**
  - Container hóa và tích hợp Odoo vào platform, kết nối PostgreSQL, CI/CD, observability.
- **Pha 6 – Docs & ADR hardening (Odoo-aware)**
  - Cập nhật kiến trúc, runbook, AI-context & ADR để Odoo trở thành sản phẩm mẫu chính thức.

Mọi pha đều phải tuân thủ:

- `delivery.small_batch.max_lines` (≈ ≤ 300 dòng thay đổi / batch),
- `delivery.trunk_based.max_branch_lifetime_hours` (branch sống < 24h),
- Luật về reliability, observability, security, infra trong `platform-laws.yaml`.

---

### 3. Pha 0 — Context & guardrail cho AI

**Mục tiêu**: Đảm bảo mỗi lần AI làm việc đều:

- Đọc đúng tài liệu nguồn (theo `cursor-system-promt.md`),
- Xác định section trong `final_devops_context.md` bị ảnh hưởng,
- Liệt kê luật áp dụng trước khi tạo patch.

**Prompt khung dùng cho mọi task (template)**:

```text
Hãy đọc theo thứ tự:
- @docs/ai-context/platform-vision.md
- @docs/ai-context/platform-laws.yaml
- @docs/ai-context/law-context-mapping.yaml
- @docs/ai-context/ai-safety-workflow.md (MANDATORY: defines your responsibilities)
- @docs/final_devops_context.md
- (các file domain-specific sẽ nêu ở dưới)

Nhiệm vụ cụ thể: [mô tả ngắn task, ví dụ: tạo skeleton docker-compose cho core infra].

LƯU Ý: Bạn chỉ được phép EXECUTE, LOG, và VERIFY. KHÔNG được checkout branch, commit, push, hoặc merge. Xem ai-safety-workflow.md để biết chi tiết.

1) Xác định:
   - final_devops_context section nào bị ảnh hưởng,
   - Các law nào trong platform-laws áp dụng (delivery, reliability, observability, security, infra).
2) Đề xuất plan thực thi ngắn gọn (3–5 bước) theo small batch (≤ ~300 lines).
3) Tự thực thi plan:
   - Tạo/chỉnh sửa file cần thiết,
   - LOG mọi hành động (theo format trong ai-safety-workflow.md),
   - Không vượt quá small batch,
   - Giải thích ngắn gọn vì sao patch tuân thủ luật.
4) Self-verify (theo ai-safety-workflow.md):
   - Constraint fit, GitOps compliance, immutable deployment, observability, documentation, small batch.
5) Generate execution summary (theo format trong ai-safety-workflow.md).
6) Nếu task đụng trade-off lớn (tài nguyên, kiến trúc), hãy tạo ADR theo @docs/ai-context/adr-template/index.md thay vì thực hiện im lặng.
```

---

### 4. Pha 1 — Skeleton platform & core infra

**Mục tiêu**:

- Cấu trúc repo & filesystem phù hợp:
  - Theo `docs/ai-context/code-generation-rules/repo-structure.yaml`,
  - Và `docs/04-environment-and-infrastructure/filesystem-layout.md`.
- Docker Compose skeleton cho:
  - Traefik (Edge),
  - PostgreSQL (Data),
  - Monitoring stack (Prometheus, Grafana, Loki),
  - (Chưa tích hợp Odoo ở pha này).

**Context cần load cho pha 1**:

- `@docs/ai-context/cursor-system-promt.md`
- `@docs/ai-context/platform-laws.yaml`
- `@docs/ai-context/law-context-mapping.yaml`
- `@docs/ai-context/code-generation-rules/repo-structure.yaml`
- `@docs/04-environment-and-infrastructure/filesystem-layout.md`
- `@docs/02-system-architecture/high-level-architecture.md`
- `@docs/03-tech-stack/tech-stack.md`

**Tasks chính**:

1. Tạo cấu trúc thư mục repo (apps, infra, scripts, v.v.).
2. Tạo `docker-compose.yml` hoặc bộ compose tương đương cho core infra.
3. Thêm stub config/thư mục cho monitoring, CI, CD (chưa chi tiết).

**Prompt gợi ý cho Task 1 (cấu trúc repo)**:

```text
Context:
- @docs/ai-context/platform-laws.yaml
- @docs/ai-context/code-generation-rules/repo-structure.yaml
- @docs/04-environment-and-infrastructure/filesystem-layout.md
- @docs/final_devops_context.md

Nhiệm vụ:
- Tạo cấu trúc thư mục repo và, nếu cần, file README/stub cho:
  - apps/
  - infra/
  - monitoring/
  - ci/
  - scripts/
  - ai-context/ (nếu cần mirror trên runtime)

Yêu cầu:
- Tuân thủ law về infra (immutable, idempotent, environment parity).
- Mỗi thay đổi không vượt quá ~300 dòng.
- Giải thích ngắn cách cấu trúc này map sang filesystem /opt/platform trong runtime.
```

**Prompt gợi ý cho Task 2 (docker-compose core infra)**:

```text
Context:
- @docs/02-system-architecture/high-level-architecture.md
- @docs/03-tech-stack/tech-stack.md
- @docs/04-environment-and-infrastructure/runtime-environment.md
- @docs/ai-context/platform-laws.yaml

Nhiệm vụ:
- Tạo một file docker-compose (hoặc tập file) cho core infra:
  - traefik (edge),
  - platform-postgres (database),
  - prometheus, grafana, loki (observability).

Yêu cầu:
- Tuân thủ 6GB RAM, tránh service mesh, tránh Kubernetes.
- Config tách khỏi image (dùng volume cho config/data, không hard-code secrets).
- Giữ patch nhỏ, và mô tả group service nào thuộc layer nào trong final_devops_context.
```

---

### 5. Pha 2 — CI/CD skeleton

**Mục tiêu**:

- CI pipeline với các stage:
  - Lint,
  - Build,
  - Test,
  - Package,
  - Security & law checks.
- Script CD triển khai docker-compose lên VM single-node, rolling update với health check.

**Context cần load**:

- `@docs/05-ci-cd/ci-architecture.md`
- `@docs/05-ci-cd/gitops-architecture.md`
- `@docs/05-ci-cd/cd-strategy.md`
- `@docs/ai-context/platform-laws.yaml`
- `@docs/ai-context/ci-enforcement/law-checks.yaml`

**Tasks chính**:

1. Chọn hệ CI mặc định (ví dụ: GitHub Actions hoặc GitLab CI) và tạo pipeline file skeleton.
2. Tạo script CD cơ bản (`scripts/deploy-platform.sh`, `scripts/rollback-platform.sh`).
3. Stub script cho security & law checks (chưa cần logic đầy đủ nhưng thể hiện hook).

**Prompt gợi ý cho Task 1 (CI pipeline)**:

```text
Context:
- @docs/05-ci-cd/ci-architecture.md
- @docs/05-ci-cd/gitops-architecture.md
- @docs/ai-context/platform-laws.yaml
- @docs/ai-context/ci-enforcement/law-checks.yaml

Nhiệm vụ:
- Tạo file pipeline CI skeleton (chọn một trong: GitHub Actions / GitLab CI).
- Bao gồm các stage: lint, build, test, package, security_and_law_checks.

Yêu cầu:
- Mỗi stage có lệnh giả (echo hoặc comment) để dễ lấp sau.
- Mô tả rõ cách stage security_and_law_checks sẽ:
  - chạy SAST,
  - dependency scan,
  - secret scan,
  - validate law-checks (small_batch, trunk_based, unit_test_present, slo_defined, telemetry_present).
- Giữ patch ≤ 300 dòng.
```

**Prompt gợi ý cho Task 2 (CD scripts)**:

```text
Context:
- @docs/05-ci-cd/cd-strategy.md
- @docs/06-deployment-strategy/deployment-pattern.md
- @docs/10-runbook/incident-response.md

Nhiệm vụ:
- Tạo script shell trong thư mục scripts/ để:
  - deploy toàn bộ platform (docker compose up với health check),
  - rollback về version trước (docker compose với image tag trước đó).

Yêu cầu:
- Script phải phù hợp immutable deployment (không patch container đang chạy).
- Có log tối thiểu và exit code rõ ràng.
- Đảm bảo tài nguyên 6GB không bị phá vỡ (ví dụ: không scale replica quá nhiều).
```

---

### 6. Pha 3 — Observability & SLO

**Mục tiêu**:

- Config tối thiểu cho:
  - Prometheus (scrape node, docker, core services),
  - Loki,
  - (Optionally) alert rules cho SLO chính.

**Context cần load**:

- `@docs/07-observability/monitoring-architecture.md`
- `@docs/07-observability/sli-slo-sla.md`
- `@docs/ai-context/platform-laws.yaml` (observability.telemetry_required)

**Tasks chính**:

1. Tạo file config Prometheus cơ bản (job cho infra + chỗ để thêm app).
2. Tạo cấu hình Loki và wiring log từ container.
3. Thêm một vài alert rule liên quan tới SLO (availability, error rate).

**Prompt gợi ý (Prometheus + SLO)**:

```text
Context:
- @docs/07-observability/monitoring-architecture.md
- @docs/07-observability/sli-slo-sla.md
- @docs/ai-context/platform-laws.yaml

Nhiệm vụ:
- Tạo config Prometheus tối thiểu:
  - job cho node/docker,
  - job cho core infra services (traefik, postgres, prometheus/grafana/loki).
- Thêm 1–2 alert rule basic theo SLO (availability, deployment success rate).

Yêu cầu:
- Giải thích cách config này đáp ứng telemetry_required (logs, metrics; traces được đánh dấu future như docs).
- Không vượt quá small batch.
```

---

### 7. Pha 4 — Sample application service (đơn giản)

**Mục tiêu**:

- Có ít nhất một service demo (ví dụ `sample-service`) để:
  - Thử CI/CD end-to-end,
  - Xuất logs + metrics,
  - Có health check + SLO cơ bản.

**Context cần load**:

- `@docs/ai-context/ai-coding-guidelines.md`
- `@docs/ai-context/golden-path/service.yaml`
- `@docs/02-system-architecture/data-flow.md`
- `@docs/11-development-guide/local-development.md`

**Tasks chính**:

1. Thiết kế `sample-service` (ngôn ngữ tùy chọn, nhưng nhẹ, phù hợp 6GB).
2. Tạo code + Dockerfile + entry trong docker-compose.
3. Hook vào CI (build/test) và monitoring (metrics/logs).
4. Update docs (system-architecture, local-development) để nhắc đến service này.

**Prompt gợi ý (service demo)**:

```text
Context:
- @docs/ai-context/ai-coding-guidelines.md
- @docs/ai-context/golden-path/service.yaml
- @docs/02-system-architecture/data-flow.md

Nhiệm vụ:
- Tạo service demo 'sample-service' (stateless HTTP API) với:
  - /health endpoint,
  - 1 endpoint business đơn giản (ví dụ /hello),
  - metrics Prometheus cơ bản (request count, latency, error count),
  - structured logs.

Yêu cầu:
- Service tuân thủ layering trong golden-path/service.yaml.
- Được add vào docker-compose và CI pipeline.
- Có test tối thiểu.
```

---

### 8. Pha 5 — Odoo integration

**Mục tiêu**:

- Chạy **Odoo** như một ứng dụng mẫu trên platform:
  - Reuse PostgreSQL hiện có (schema/DB riêng),
  - Được expose qua Traefik,
  - Có CI/CD cơ bản,
  - Có observability & SLO tối thiểu.

**Lưu ý về constraint**:

- Odoo khá nặng, cần đặc biệt chú ý:
  - Memory footprint trong 6GB RAM (xem `runtime-environment.md`),
  - Có thể cần ADR nếu resource usage quá lớn.

**Context cần load**:

- Toàn bộ context trước (Pha 1–4), cộng thêm:
  - `@docs/03-tech-stack/tech-stack-decision.md` (lý do chọn công nghệ),
  - `@docs/08-security/security-baseline.md`,
  - Bất kỳ tài liệu Odoo official (qua web_search nếu cần).

**Tasks chính**:

1. **Thiết kế kiến trúc tích hợp Odoo**:
   - Odoo app container,
   - Reuse `platform-postgres` với DB/schema riêng cho Odoo,
   - Expose qua Traefik với host/path riêng.
   - Đánh giá sơ bộ memory usage và tạo ADR nếu sát ngưỡng 6GB.
2. **Implement Odoo service**:
   - Docker image (dùng official image + minimal config),
   - docker-compose service,
   - environment configuration (DB conn, admin user).
3. **CI/CD cho Odoo**:
   - Job build/pull Odoo image (nếu cần custom),
   - Test sanity (healthcheck, basic HTTP check),
   - CD hook deploy/rollback Odoo.
4. **Observability & SLO cho Odoo**:
   - Logs gửi về Loki,
   - Metrics (if available) hoặc ít nhất exporter/side metrics,
   - Định nghĩa SLO basic cho web UI (availability, latency).

**Prompt gợi ý (thiết kế tích hợp Odoo + ADR)**:

```text
Context:
- @docs/ai-context/cursor-system-promt.md
- @docs/ai-context/platform-laws.yaml
- @docs/ai-context/law-context-mapping.yaml
- @docs/final_devops_context.md
- @docs/03-tech-stack/tech-stack-decision.md
- @docs/04-environment-and-infrastructure/runtime-environment.md

Nhiệm vụ:
- Đề xuất kiến trúc tích hợp Odoo vào Nano DevOps Platform:
  - Odoo container + kết nối tới platform-postgres,
  - Routing qua Traefik,
  - Ước lượng RAM/CPU để đảm bảo vẫn trong 6GB tổng.

Yêu cầu:
- Thực hiện STEP 1–2–3–4 trong cursor-system-promt (context, law validation, golden-path, architecture check).
- Nếu resource risk cao, hãy tạo ADR theo @docs/ai-context/adr-template/index.md để ghi rõ trade-off,
  trước khi implement chi tiết.
```

**Prompt gợi ý (implement Odoo service)**:

```text
Context:
- (ADR đã được chấp nhận nếu có)
- @docs/ai-context/ai-coding-guidelines.md
- @docs/02-system-architecture/high-level-architecture.md

Nhiệm vụ:
- Thêm service 'odoo' vào docker-compose:
  - Sử dụng image Odoo official (hoặc một biến thể nhẹ),
  - Kết nối tới PostgreSQL hiện có (DB/schema riêng),
  - Expose qua Traefik.
- Cập nhật CI/CD để:
  - build/pull image đúng version,
  - kiểm tra health endpoint của Odoo sau deploy.

Yêu cầu:
- Tuân thủ small batch (chia thành nhiều patch nếu cần).
- Mô tả rõ Odoo thuộc layer nào trong kiến trúc (Application Layer).
```

---

### 9. Pha 6 — Docs & ADR hardening (Odoo-aware)

**Mục tiêu**:

- Toàn bộ hệ thống docs phản ánh việc:
  - Odoo là sản phẩm mẫu chính,
  - Platform có thể demo năng lực DevOps/Platform/SRE thông qua Odoo.

**Context cần load**:

- `@docs/final_devops_context.md`
- `@docs/02-system-architecture/*`
- `@docs/03-tech-stack/*`
- `@docs/10-runbook/incident-response.md`
- `@docs/11-development-guide/*`
- `@docs/ai-context/*`

**Tasks chính**:

1. Cập nhật `system-overview`, `high-level-architecture`, `logical-architecture` để thể hiện Odoo là một ứng dụng chạy trên platform.
2. Cập nhật `tech-stack` để nhắc tới Odoo (như “sample business app”).
3. Cập nhật `local-development` & `contribution-guide` để hướng dẫn:
   - Chạy platform + Odoo locally,
   - Quy tắc thay đổi liên quan tới Odoo.
4. Cập nhật `ai-coding-guidelines.md` & `system-context.md` (nếu cần) để:
   - Cho phép AI hiểu Odoo là một dịch vụ ứng dụng,
   - Biết giới hạn thay đổi (không phá core runtime, không vượt budget).

**Prompt gợi ý (refactor docs sau Odoo)**:

```text
Context:
- @docs/final_devops_context.md
- @docs/02-system-architecture/high-level-architecture.md
- @docs/02-system-architecture/logical-architecture.md
- @docs/03-tech-stack/tech-stack.md
- @docs/11-development-guide/local-development.md

Nhiệm vụ:
- Cập nhật docs để:
  - Thêm Odoo vào các diagram/flow chính như một ứng dụng mẫu,
  - Giải thích ngắn use-case: dùng Odoo để chứng minh năng lực platform.

Yêu cầu:
- Không thay đổi constraint cốt lõi (single-node, 6GB).
- Thay đổi theo small batch, và mỗi patch phải nêu rõ law nào đang được giữ/được kiểm tra.
```

---

### 10. Cách sử dụng file kế hoạch này

**IMPORTANT**: Đọc `ai-safety-workflow.md` trước khi bắt đầu. Workflow này đảm bảo AI chỉ execute/log/verify, còn bạn quyết định Git operations.

- **Khi bắt đầu một batch công việc mới**:
  1. **Bạn**: Chọn **pha** + **task** trong file này
  2. **Bạn**: Tạo feature branch:
     ```bash
     git checkout -b feat/phase1-task1
     ```
  3. **Bạn**: Copy prompt gợi ý tương ứng vào Cursor, thêm note về ai-safety-workflow.md
  4. **AI**: Tự động thực thi (tạo/chỉnh file), log actions, self-verify, generate summary
  5. **Bạn**: Review execution log và git diff
  6. **Bạn**: Commit và merge (nếu approved):
     ```bash
     git add .
     git commit -m "feat: [task description]"
     git push origin feat/phase1-task1
     # Create PR, review, merge
     ```
- **Khi close một pha**:
  - Đảm bảo:
    - Docs trong `final_devops_context.md` vẫn còn đúng,
    - Không có vi phạm rõ ràng với `platform-laws.yaml`,
    - Nếu có trade-off lớn, đã có ADR trong `ai-context/adr-template/`,
    - Tất cả execution logs đã được review.

File này là **roadmap sống**: có thể (và nên) được cập nhật khi platform tiến hóa, nhưng mọi chỉnh sửa cũng phải tuân thủ cùng luật small batch / trunk-based như phần còn lại của dự án.




==================================================
SOURCE_PATH: ./docs-ai-context/ai-safety-workflow.md
==================================================
# AI Safety Workflow

This document defines the **safety workflow** for AI-assisted development on the Nano DevOps Platform. It ensures that AI-generated changes are **logged, verified, and reviewed** before affecting production, while clearly separating **AI responsibilities** from **human decision-making**.

---

## 1. Core Safety Principles

- **AI executes, humans decide**: AI performs tasks, logs actions, and verifies results. Humans control Git operations (branching, merging, deployment).
- **Nothing touches production without review**: All changes go through a reviewable branch and explicit human approval.
- **Full audit trail**: Every AI action must be logged and traceable.
- **Fail-safe defaults**: If verification fails, AI must stop and report, not proceed.

---

## 2. Workflow Overview

```text
Human: Select task from ai-platform-build-plan.md
  ↓
Human: Create feature branch (e.g., feat/phase1-task1)
  ↓
AI: Read context (platform-laws, final_devops_context, etc.)
  ↓
AI: Execute task (create/modify files)
  ↓
AI: Log all actions (what was changed, why, which laws applied)
  ↓
AI: Self-verify (constraints, laws, small batch)
  ↓
AI: Generate summary report
  ↓
Human: Review changes (diff, logs, summary)
  ↓
Human: Run local tests (if applicable)
  ↓
Human: Merge to main (if approved)
  ↓
CI/CD: Automated validation & deployment
```

---

## 3. AI Responsibilities (What AI Must Do)

### 3.1 Before Starting Any Task

AI **must**:

1. **Load required context** (in order):
   - `ai-context/platform-vision.md`
   - `ai-context/platform-laws.yaml`
   - `ai-context/law-context-mapping.yaml`
   - `final_devops_context.md` (relevant sections)
   - Domain-specific docs as needed

2. **Identify affected sections**:
   - Which `final_devops_context` section(s) are impacted
   - Which platform laws apply (delivery, reliability, observability, security, infra)

3. **Propose execution plan** (3–5 steps, ≤ 300 lines total):
   - List files to create/modify
   - Explain why each change is needed
   - Confirm small batch compliance

### 3.2 During Execution

AI **must**:

1. **Execute changes**:
   - Create/modify files as planned
   - Follow golden-path templates when applicable
   - Respect platform laws and constraints

2. **Log every action**:
   - What file was created/modified
   - What content was added/changed (brief summary)
   - Which platform law(s) this change enforces
   - Estimated resource impact (if applicable)

3. **Self-verify before completion**:
   - ✅ Constraint fit (6GB RAM, single-node)
   - ✅ GitOps compliance (all changes in Git, no manual-only steps)
   - ✅ Immutable deployment (no runtime patching)
   - ✅ Observability coverage (metrics/logs if new service)
   - ✅ Documentation updated (if needed)
   - ✅ Small batch (≤ 300 lines changed)

### 3.3 After Execution

AI **must**:

1. **Generate execution summary**:
   - List all files changed (with paths)
   - Summary of changes (what was done)
   - Laws applied and verified
   - Resource impact assessment (if applicable)
   - Any warnings or trade-offs

2. **Report verification status**:
   - ✅ All checks passed, or
   - ⚠️ Warnings (non-blocking), or
   - ❌ Blocking issues (must stop)

3. **Never**:
   - Checkout branches
   - Commit changes
   - Push to remote
   - Merge branches
   - Deploy to production

---

## 4. Human Responsibilities (What Humans Must Do)

### 4.1 Before AI Execution

Human **must**:

1. **Select task** from `ai-platform-build-plan.md`
2. **Create feature branch**:
   ```bash
   git checkout -b feat/phase1-task1
   ```
3. **Provide clear prompt** to AI:
   - Reference the task from build plan
   - Specify any additional context or constraints
   - Confirm AI should proceed

### 4.2 After AI Execution

Human **must**:

1. **Review AI-generated summary**:
   - Check execution log
   - Verify files changed match expectations
   - Confirm laws were applied correctly

2. **Inspect changes**:
   ```bash
   git status
   git diff
   ```
   - Review file-by-file changes
   - Verify no unintended modifications
   - Check for hardcoded secrets, resource violations, etc.

3. **Run local verification** (if applicable):
   - Lint/format checks
   - Local tests
   - Docker Compose validation (if infra changes)

4. **Decide on merge**:
   - ✅ **Approve**: Commit and prepare for merge
   - ⚠️ **Request changes**: Ask AI to fix issues
   - ❌ **Reject**: Discard branch, start over

5. **Commit and merge** (if approved):
   ```bash
   git add .
   git commit -m "feat: [task description]"
   git push origin feat/phase1-task1
   # Create PR, review, merge to main
   ```

---

## 5. Execution Log Format

AI must generate a log in this format for every task:

```markdown
## AI Execution Log

**Task**: [Task name from build plan]
**Branch**: [Current branch name - AI reads from git, does not create]
**Timestamp**: [ISO 8601 format]

### Context Loaded
- ✅ ai-context/platform-vision.md
- ✅ ai-context/platform-laws.yaml
- ✅ final_devops_context.md (sections: [list])

### Laws Applied
- delivery.small_batch (max_lines: 300)
- [other applicable laws]

### Execution Plan
1. [Step 1]
2. [Step 2]
...

### Files Changed
- `path/to/file1`: Created/Modified - [brief description]
- `path/to/file2`: Modified - [brief description]

### Verification Results
- ✅ Constraint fit: [explanation]
- ✅ GitOps compliance: [explanation]
- ✅ Immutable deployment: [explanation]
- ✅ Observability: [explanation if applicable]
- ✅ Small batch: [X lines changed, ≤ 300]

### Resource Impact
- Memory: [estimate if applicable]
- CPU: [estimate if applicable]

### Warnings
- [Any non-blocking warnings]

### Blocking Issues
- [Any issues that prevent merge - if none, state "None"]

### Summary
[2-3 sentence summary of what was done and why it's safe]
```

---

## 6. Safety Checks (AI Must Verify)

Before reporting completion, AI must verify:

### 6.1 Constraint Compliance
- ✅ Total memory impact ≤ 6GB (if adding services)
- ✅ No Kubernetes/service mesh introduced
- ✅ No per-service databases (unless justified)
- ✅ Single-node compatible

### 6.2 Law Compliance
- ✅ Small batch (≤ 300 lines changed)
- ✅ Trunk-based (branch lifetime < 24h - human responsibility, but AI notes)
- ✅ Unit tests present (if code changes)
- ✅ SLO/telemetry configured (if new service)
- ✅ Security scans pass (if CI changes)

### 6.3 GitOps Compliance
- ✅ All changes represented in Git
- ✅ No manual-only configuration paths
- ✅ No direct VM edits suggested
- ✅ Rollback path exists (previous image version)

### 6.4 Documentation
- ✅ Relevant docs updated (if behavior changes)
- ✅ Architecture diagrams updated (if structure changes)
- ✅ Runbooks updated (if operational changes)

---

## 7. Failure Modes and Responses

### 7.1 AI Detects Blocking Issue

**AI must**:
- Stop execution immediately
- Report the issue in execution log
- Explain why it's blocking
- Suggest remediation (if possible)

**Human must**:
- Review the blocking issue
- Decide: fix, workaround, or abandon task

### 7.2 Verification Fails

**AI must**:
- Report which check(s) failed
- Explain impact
- Suggest fixes

**Human must**:
- Review failures
- Request AI to fix, or fix manually
- Re-run verification

### 7.3 Resource Budget Exceeded

**AI must**:
- Stop before creating resource-heavy components
- Report estimated usage vs. budget
- Suggest alternatives or ADR

**Human must**:
- Review resource analysis
- Approve constraint change (via ADR), or request redesign

---

## 8. Integration with CI/CD

After human merges to `main`:

1. **CI pipeline runs**:
   - Lint, build, test, package
   - Security & law checks
   - If any stage fails → human must fix

2. **CD pipeline runs** (if CI passes):
   - Deploy to single-node VM
   - Health checks
   - Rollback if health checks fail

3. **AI is not involved** in CI/CD execution (automated)

---

## 9. Example: Complete Workflow

### Step 1: Human Creates Branch
```bash
git checkout -b feat/phase1-task1-skeleton-repo
```

### Step 2: Human Provides Prompt
```
Execute Phase 1 - Task 1 from ai-platform-build-plan.md:
- Create repo skeleton (apps/, infra/, scripts/, etc.)
- Follow repo-structure.yaml and filesystem-layout.md
- Keep changes ≤ 300 lines
- Generate execution log
```

### Step 3: AI Executes
- Loads context
- Creates directories and stub files
- Generates execution log
- Self-verifies
- Reports completion

### Step 4: Human Reviews
```bash
git status
git diff
# Review execution log
# Verify no violations
```

### Step 5: Human Commits (if approved)
```bash
git add .
git commit -m "feat: init platform skeleton (phase1-task1)"
git push origin feat/phase1-task1-skeleton-repo
```

### Step 6: Human Creates PR
- Review PR diff
- CI runs automatically
- Merge if CI passes

### Step 7: CD Deploys (automated)
- CD pipeline runs
- Deploys to VM
- Health checks verify

---

## 10. Best Practices

### For Humans
- **Always review execution log** before committing
- **Test locally** before merging (if applicable)
- **Keep branches short-lived** (< 24h per platform laws)
- **One task per branch** (small batch principle)

### For AI
- **Never skip verification steps**
- **Always log actions** (even if trivial)
- **Report warnings** (don't hide issues)
- **Stop on blocking issues** (don't proceed hoping human will catch it)

---

## 11. Emergency Procedures

### If AI Makes Unintended Changes

1. **Human stops AI** (if still running)
2. **Review git diff**:
   ```bash
   git diff
   git status
   ```
3. **Discard unwanted changes**:
   ```bash
   git checkout -- <file>
   # or
   git reset --hard HEAD
   ```
4. **Restart task** with clearer prompt

### If Changes Are Merged but Cause Issues

1. **Rollback via GitOps**:
   ```bash
   git revert <commit-hash>
   git push
   ```
2. **CD automatically redeploys** previous version
3. **Investigate** root cause (was it AI error or missing context?)

---

## 12. Continuous Improvement

- **After each task**: Review execution log quality
- **After each phase**: Assess if workflow needs adjustment
- **Update this workflow** if patterns emerge (via PR, following same workflow)

---

This workflow ensures that **AI assists safely** while **humans maintain control** over all Git operations and production deployments.



==================================================
SOURCE_PATH: ./docs-ai-context/ci-enforcement/law-checks.yaml
==================================================
checks:

  - name: slo_defined
  - name: telemetry_present
  - name: unit_test_present
  - name: small_batch
  - name: trunk_based


==================================================
SOURCE_PATH: ./docs-ai-context/code-generation-rules/repo-structure.yaml
==================================================
when_create_repo:

  create:
    - apps/
    - platform/
    - infra/
    - ai-context/


==================================================
SOURCE_PATH: ./docs-ai-context/code-generation-rules/service-scaffold.yaml
==================================================
when_create_service:

  use_golden_path: service.yaml

  auto_generate:
    - healthcheck
    - telemetry
    - slo_config
    - test_structure


==================================================
SOURCE_PATH: ./docs-ai-context/cursor-system-promt.md
==================================================
# CURSOR SYSTEM PROMPT — PLATFORM ENGINEERING MODE

## 1. ROLE

You are not a generic coding assistant.

You are:

* a Platform Engineer
* a DevOps architect
* an SRE-aware system designer

Your job is to:

* build and refactor the system according to PLATFORM LAWS
* enforce architectural consistency
* optimize for delivery performance and reliability

You must NEVER generate code that violates platform laws.

---

## 2. SOURCE OF TRUTH (MANDATORY READING ORDER)

Before any action, you MUST read in this exact order:

1. ai-context/platform-vision.md
2. ai-context/platform-laws.yaml
3. ai-context/law-context-mapping.yaml

Then load:

4. golden-path/*
5. decision-trees/*
6. slo/*
7. code-generation-rules/*

For detailed guidelines and context:

8. ai-context/system-context.md
9. ai-context/ai-coding-guidelines.md
10. ai-context/ai-platform-build-plan.md (when planning major changes)
11. ai-context/ai-safety-workflow.md (MANDATORY: defines execution, logging, verification responsibilities)

If context is missing → STOP and ask.

---

## 3. GENERATION WORKFLOW

**CRITICAL**: You are an **executor and verifier**, NOT a Git operator. You **MUST NOT** checkout branches, commit, push, or merge. See `ai-safety-workflow.md` for full details.

For every request:

### STEP 1 — CONTEXT RESOLUTION

Identify:

* which final_devops_context section is affected
* which laws apply

### STEP 2 — LAW VALIDATION

Check:

* Is the change allowed by platform laws?
* Does it break DORA / SRE targets?
* Does it increase cognitive load?

If violation → propose compliant alternative.

### STEP 3 — GOLDEN PATH EXECUTION

If creating:

* service → use golden-path/service.yaml
* pipeline → use golden-path/pipeline.yaml
* environment → use golden-path/environment.yaml

Never invent structure.

### STEP 4 — ARCHITECTURE CHECK

All code must follow:

* stateless services
* explicit data flow
* clean architecture layering
* testability

### STEP 5 — EXECUTION & LOGGING (MANDATORY)

After making changes:

1. **Log every action**:
   - What files were created/modified
   - What content was changed (brief summary)
   - Which platform laws were applied
   - Resource impact (if applicable)

2. **Self-verify**:
   - ✅ Constraint fit (6GB RAM, single-node)
   - ✅ GitOps compliance (all changes in Git)
   - ✅ Immutable deployment (no runtime patching)
   - ✅ Observability coverage (if new service)
   - ✅ Documentation updated (if needed)
   - ✅ Small batch (≤ 300 lines changed)

3. **Generate execution summary**:
   - List all files changed
   - Summary of changes
   - Laws applied and verified
   - Verification status (✅/⚠️/❌)
   - Any warnings or blocking issues

4. **Never**:
   - Checkout branches
   - Commit changes
   - Push to remote
   - Merge branches
   - Deploy to production

See `ai-safety-workflow.md` for the complete execution log format.

---

## 4. DELIVERY PERFORMANCE OPTIMIZATION

Always optimize for:

* small batch changes
* trunk-based development
* fast feedback loops
* deployability

Reject designs that:

* require big-bang integration
* create long-lived branches
* hide integration risk

---

## 5. SRE & RELIABILITY MODE

Every runtime component MUST include:

* health check
* telemetry (logs, metrics, traces)
* SLO definition

If missing → auto-generate.

Apply error budget policy to release decisions.

---

## 6. OBSERVABILITY-FIRST DEVELOPMENT

Features are NOT complete until:

* measurable via SLIs
* observable in runtime

---

## 7. SECURITY BY DEFAULT

All pipelines MUST include:

* SAST
* dependency scan
* secret detection

Never generate insecure defaults.

---

## 8. INFRASTRUCTURE RULES

Infrastructure must be:

* immutable
* idempotent
* environment parity compliant

No manual mutation.

---

## 9. ADR REQUIREMENT

When a trade-off appears:

You MUST:

* generate an ADR
* explain:

  * context
  * decision
  * trade-offs
  * consequences

---

## 10. OUTPUT MODE

When generating:

### For code:

Explain:

* which laws are applied
* why the structure is chosen

### For refactoring:

Show:

* law violations detected
* compliant redesign

---

## 11. ANTI-GOALS

You must NOT:

* generate quick hacks
* optimize for local simplicity over system flow
* introduce hidden state
* bypass CI enforcement
* perform Git operations (checkout, commit, push, merge) — these are human responsibilities
* skip logging or verification steps
* proceed when verification fails (must stop and report)

---

## 12. SUCCESS CRITERIA

Your output increases:

* deployment frequency
* system reliability
* developer experience
* architectural consistency

If not → redesign.



==================================================
SOURCE_PATH: ./docs-ai-context/decision-trees/consistency.yaml
==================================================
rules:

  - condition: financial_transaction
    result: strong_consistency

  - condition: multi_region
    result: eventual_consistency


==================================================
SOURCE_PATH: ./docs-ai-context/decision-trees/scaling.yaml
==================================================
rules:

  - condition: read_heavy
    result: read_replica

  - condition: write_heavy
    result: sharding


==================================================
SOURCE_PATH: ./docs-ai-context/final_ai_context.md
==================================================



==================================================
SOURCE_PATH: ./docs-ai-context/get_final_ai_context.sh
==================================================



==================================================
SOURCE_PATH: ./docs-ai-context/golden-path/environment.yaml
==================================================
environments:
  - dev
  - staging
  - prod

parity: required
config_externalized: true


==================================================
SOURCE_PATH: ./docs-ai-context/golden-path/pipeline.yaml
==================================================
stages:
  - validate_laws
  - unit_test
  - build
  - security_scan
  - deploy

policies:
  fail_on_missing_test: true
  fail_on_large_change: true


==================================================
SOURCE_PATH: ./docs-ai-context/golden-path/service.yaml
==================================================
service:
  structure:
    layers:
      - domain
      - application
      - infrastructure

  runtime:
    healthcheck: required
    resource_limits: required

  observability:
    logs: structured
    metrics: enabled
    traces: enabled

  reliability:
    slo: required


==================================================
SOURCE_PATH: ./docs-ai-context/law-context-mapping.yaml
==================================================
foundation:
  - delivery.small_batch
  - delivery.trunk_based

service_template:
  - reliability.slo_required
  - observability.telemetry_required
  - architecture.stateless_service

ci_cd:
  - delivery.testability
  - security.secure_pipeline

runtime:
  - infra.immutable

observability:
  - reliability.error_budget_policy


==================================================
SOURCE_PATH: ./docs-ai-context/platform-laws.yaml
==================================================
delivery:
  small_batch:
    max_lines: 300

  trunk_based:
    max_branch_lifetime_hours: 24

  testability:
    unit_test_required: true

reliability:
  slo_required: true
  error_budget_policy: enforced

architecture:
  stateless_service: true
  explicit_data_flow: true

observability:
  telemetry_required:
    - logs
    - metrics
    - traces

security:
  secure_pipeline:
    - sast
    - dependency_scan
    - secret_scan

infra:
  immutable: true
  idempotent: true


==================================================
SOURCE_PATH: ./docs-ai-context/platform-vision.md
==================================================
# PLATFORM VISION

The platform is treated as a product.

Primary users: application developers  
Goal: reduce cognitive load and enable fast, safe delivery.

## Core Principles

- Self-service over manual ops
- Golden path is the default
- Everything measurable
- Small batch changes
- Trunk-based development
- Reliability as a feature

## Delivery Performance Targets (DORA)

Deployment frequency: daily  
Lead time for change: < 1 day  
MTTR: < 1 hour  
Change failure rate: < 15%

## SRE Runtime Targets

Every service must define:
- SLI
- SLO
- Error budget

Toil < 30%


==================================================
SOURCE_PATH: ./docs-ai-context/slo/error-budget-policy.yaml
==================================================
error_budget:

  burn_rate_threshold: 2

actions_on_exhaustion:
  - freeze_release
  - focus_on_reliability


==================================================
SOURCE_PATH: ./docs-ai-context/slo/slo-template.yaml
==================================================
slo:
  availability: 99.9
  latency_p95_ms: 300
  error_rate: 1%


==================================================
SOURCE_PATH: ./docs-ai-context/system-context.md
==================================================
# AI System Context

This document defines the minimal context an AI agent (e.g. Cursor) needs to safely propose and implement changes on the Nano DevOps Platform while respecting the **single-node 6GB constraint**, **GitOps**, and **immutable deployment** principles defined in `platform-master-strategy.md`.

---

## 1. Repository and Filesystem Overview

### 1.1 Repositories

- **Platform repo (this repo)**:  
  - Contains:
    - Infrastructure as code (Docker / docker-compose, runtime scripts)
    - Platform services definitions
    - CI/CD definitions
    - Documentation (`/docs`)
  - **Git is the only source of truth** for platform state.

### 1.2 Filesystem Layout on VM

See `filesystem-layout.md` for details. High-level:

```text
/opt/platform
  ├── apps            # Application services (per-service folders)
  ├── data            # Persistent data (e.g. PostgreSQL volumes)
  ├── monitoring      # Prometheus / Grafana / Loki config & data
  ├── ci              # CI/CD runner and related scripts
  └── scripts         # Operational automation (deploy, backup, restore, etc.)
```

AI agents should **treat this structure as stable** and only modify files where explicitly allowed below.

---

## 2. Naming Conventions

- **Services**
  - Lowercase, hyphen-separated, short but descriptive.  
    - Examples: `user-service`, `billing-api`, `reporting-worker`.
- **Docker Compose service names**
  - Match application service names where possible, with suffixes for infrastructure when needed.  
    - Examples: `user-service`, `platform-postgres`, `platform-prometheus`.
- **Monitoring artifacts**
  - Prometheus job names follow `layer-service` style.  
    - Example: `app-user-service`, `infra-traefik`.
- **Scripts**
  - Use verb-noun form and be explicit about scope.  
    - Examples: `deploy-service.sh`, `rollback-service.sh`, `backup-db.sh`, `restore-db.sh`.

---

## 3. Deployment Flow (GitOps and Immutable)

The only safe way for AI to change the running system is through **Git → CI → CD → Runtime**.

```text
Developer / AI
    ↓ (1) Git commit + PR
Git repository
    ↓ (2) CI pipeline (lint → build → test → package)
Container registry
    ↓ (3) CD pipeline (pull image → health check → switch traffic)
Runtime (Docker on single-node VM)
```

- **Step 1 – Git change**
  - All configuration and code changes are committed to Git.
  - No direct modification of files on `/opt/platform` by hand.
- **Step 2 – CI**
  - Builds container images and runs tests.
  - Produces versioned artifacts (immutable images).
- **Step 3 – CD**
  - Pulls the new image, performs health checks, and switches traffic using rolling update (see `deployment-pattern.md`).
  - Old versions are removed only after successful verification.

AI proposals **must not** bypass this flow.

---

## 4. Service Dependency Map (Conceptual)

For full details see `high-level-architecture.md` and `logical-architecture.md`. Quick textual view:

```text
          Internet User
                │
                ▼
          [Traefik Edge]
                │
                ▼
         [App Services]*  ────►  [PostgreSQL]
                │
                └────────►  [Monitoring Exporters]

CI/CD:
Developer / AI
    │
    ▼
   [Git]
    │
    ▼
 [CI Pipeline] ──► [Image Registry] ──► [CD Scripts] ──► [Docker Runtime]

Observability:
Services ─► [Prometheus] ─► [Grafana]
Logs    ─► [Loki]
Alerts  ─► Alert rules (Prometheus / Grafana)
```

- All app services:
  - Receive traffic only via the reverse proxy.
  - Use **shared PostgreSQL** (no per-service DB by default).
  - Export metrics and logs into the shared monitoring stack.

---

## 5. Allowed Operations for AI

AI agents may:

- **Create or modify application services** under the designated app/service configuration areas:
  - Add/update service definitions in the appropriate Docker Compose file(s) **for application layer only**.
  - Add/update app code within `/opt/platform/apps/<service-name>` (via Git).
- **Extend observability for services**:
  - Add Prometheus scrape configs for new services.
  - Add/update dashboards for new services.
- **Update documentation**:
  - Extend `docs` to describe new services, flows, and runbooks.
- **Modify CI config for new services**:
  - Add jobs/stages so new services are built, tested, and packaged consistently with existing ones.

All changes must **respect resource constraints** and **follow GitOps**.

---

## 6. Forbidden Actions for AI

The following are strictly **forbidden** for AI agents:

- **Core runtime and infrastructure**
  - Do not modify:
    - Core Docker runtime configuration (e.g. base Docker daemon settings).
    - Core infrastructure compose/services for:
      - Traefik
      - PostgreSQL
      - Prometheus / Grafana / Loki
      - CI runner
  - Do not change network topology (ports, network modes) for core components.
- **Resource model violations**
  - Do not introduce:
    - New always-on services that would obviously exceed the **6GB RAM** budget.
    - Per-service databases by default (see `ai-coding-guidelines.md`).
    - Heavy sidecar patterns that duplicate functionality of existing shared infrastructure.
- **Bypassing GitOps**
  - Do not:
    - Directly edit files on `/opt/platform` outside of Git workflows.
    - Suggest manual `docker exec` or in-container changes as permanent fixes.
    - Apply ad-hoc configuration changes that are not represented in Git.
- **Modifying platform design fundamentals**
  - Do not:
    - Introduce Kubernetes or service mesh.
    - Change the single-node / 6GB constraint assumptions.
    - Modify global security baselines (non-root containers, secrets handling, network isolation).

If a required change appears to need any of the above, the AI must instead:

- Document the limitation,
- Propose a **human-reviewed design change** as a separate architectural decision, not an automated code change.

---

## 7. Safe Change Checklist for AI

Before proposing or applying a change, an AI agent should verify:

1. **Constraint fit**
   - Estimated memory impact keeps total usage within the budget in `runtime-environment.md`.
   - No new long-running processes that significantly increase idle resource usage.
2. **GitOps compliance**
   - All modifications are represented as Git changes.
   - No instruction requires out-of-band manual edits on the VM.
3. **Immutable deployment**
   - Changes are rolled out via new container images, not by mutating running containers.
4. **Observability coverage**
   - New services expose metrics/logs consistent with existing standards.
   - Dashboards and alerts are updated if needed.
5. **Documentation**
   - Relevant docs in `/docs` are updated to reflect new behaviour and dependencies.

Only when all the above are satisfied should an AI proceed to suggest or orchestrate changes.



==================================================
SOURCE_PATH: ./docs-devops/00-overview/platform-constraints.md
==================================================
# Platform Constraints

## Hard Limits

- Single node
- 6GB RAM
- Limited disk I/O

## Design Impact

- No Kubernetes
- No heavy service mesh
- Minimal container count
- Priority on vertical efficiency


==================================================
SOURCE_PATH: ./docs-devops/00-overview/platform-master-strategy.md
==================================================
# 1. Mission

Xây dựng một self-hosted DevOps platform chạy trên single-node (6GB RAM) nhưng vẫn đạt tiêu chuẩn production về:

- CI/CD
- Deployment reliability
- Observability
- Disaster recovery
- Security baseline

System đóng vai trò:

- Production-like lab
- Platform engineering showcase
- AI-operable infrastructure

---

# 2. Core Philosophy

## 2.1 Constraint-Driven Design

Hard constraints:

- Single VM
- 6GB RAM
- No horizontal scaling

Mọi quyết định kỹ thuật phải tối ưu:

- Memory footprint
- Idle resource usage
- Operational simplicity

## 2.2 GitOps First

- Git là source of truth
- Không thay đổi trực tiếp trên runtime

## 2.3 Immutable Deployment

- Không patch container đang chạy
- Mọi thay đổi = build version mới

## 2.4 Observability First

System không có monitoring = system không tồn tại.

## 2.5 Automation First

Manual operation phải:

- script hóa
- hoặc pipeline hóa

---

# 3. Platform Goals

## 3.1 Technical Goals

- Zero-downtime deployment
- Rollback < 1 minute
- Fully containerized runtime
- Reproducible environment
- Fast disaster recovery

## 3.2 Resource Goals

Total RAM: 6GB

Phân bổ:

- Reverse proxy
- CI runner (burst)
- Application
- Database
- Monitoring
- Buffer

## 3.3 Operational Goals

- Onboard dev mới < 1 ngày
- AI có thể đọc docs và generate service đúng chuẩn
- Debug trong < 15 phút

---

# 4. Non-Goals

System này KHÔNG nhằm:

- Build HA cluster
- Multi-region deployment
- Cloud managed services

---

# 5. Architecture Principles

## 5.1 Single-node optimized

Không dùng:

- Kubernetes
- Service mesh
- Heavy sidecar

## 5.2 Stateless application layer

State nằm ở:

- Database
- Volume

## 5.3 Externalized configuration

Config tách khỏi image.

## 5.4 Health-check driven deployment

Chỉ switch traffic khi service healthy.

---

# 6. Logical Architecture

Platform gồm các layer:

1. Edge Layer
2. Compute Layer
3. Application Layer
4. Data Layer
5. CI/CD Layer
6. Observability Layer

---

# 7. CI/CD Strategy

Pipeline phải:

- Declarative
- Reproducible
- Artifact-based

Flow:

Code → Build → Test → Package → Release → Deploy → Verify

Rollback:

- Redeploy previous artifact

---

# 8. Deployment Strategy

Pattern:

Rolling update with health check.

Goals:

- Zero downtime
- Fast rollback
- Minimal resource spike

---

# 9. Observability Strategy

## 9.1 Metrics

Phải monitor:

- CPU
- Memory
- Disk
- Container health
- Application latency

## 9.2 Logs

- Centralized
- Searchable

## 9.3 Alerts

Alert khi:

- Service down
- Resource saturation
- Deployment failure

---

# 10. Disaster Recovery Strategy

## 10.1 Backup

- Automated
- Versioned

## 10.2 Restore

Restore phải:

- Scriptable
- Tested

Targets:

- RTO < 1h
- RPO < 24h

---

# 11. Security Baseline

- Non-root container
- Secrets không hard-code
- Minimal exposed ports
- Internal network isolation

---

# 12. AI-Operable Platform

Docs phải đủ để AI:

Hiểu:

- System structure
- Deployment flow
- Service dependency

AI phải bị cấm:

- Thêm service vượt resource budget
- Sửa core runtime

---

# 13. Documentation Standards

Docs phải:

- Là source of truth
- Up-to-date với runtime
- Có diagram cho mọi flow quan trọng

---

# 14. Definition of Done (Platform Level)

Platform được coi là hoàn thiện khi:

- Deploy không downtime
- Rollback < 1 phút
- Monitoring đầy đủ
- Backup restore test thành công
- Dev mới onboard theo docs chạy được system
- AI generate service đúng chuẩn

---

# 15. Target Outcome

Platform thể hiện năng lực:

- DevOps Engineer (automation & CI/CD)
- Platform Engineer (system design)
- SRE mindset (reliability & observability)
- FinOps mindset (resource efficiency)


==================================================
SOURCE_PATH: ./docs-devops/00-overview/system-overview.md
==================================================
# System Overview

## Purpose

Nano DevOps Platform là một self-hosted DevOps environment được thiết kế để:

- Triển khai ứng dụng với zero-downtime
- Tối ưu tài nguyên (6GB RAM constraint)
- Chuẩn hoá CI/CD
- Cung cấp observability đầy đủ
- Sẵn sàng migrate lên cloud hoặc Kubernetes

## Core Values

- Automation First
- GitOps Driven
- Resource Efficiency
- Production-like Environment
- Self-healing mindset

## Target Users

- DevOps Engineers
- Backend Developers
- AI Agents
- System Operators

## System Scope

System bao gồm:

- Source Control
- CI/CD Pipeline
- Container Runtime
- Reverse Proxy
- Application Services
- Database
- Monitoring & Logging
- Backup & Restore

## Out of Scope

- Multi-region deployment
- High availability cluster
- Cloud-managed services


==================================================
SOURCE_PATH: ./docs-devops/01-vision-and-philosophy/design-principles.md
==================================================
# Design Principles

- Zero-downtime deployment
- Rollback under 1 minute
- Stateless application layer
- Externalized configuration
- Containerized runtime
- Declarative CI/CD pipeline


==================================================
SOURCE_PATH: ./docs-devops/01-vision-and-philosophy/engineering-philosophy.md
==================================================
# Engineering Philosophy

This document defines the core engineering principles for the Nano DevOps Platform. All technical decisions, implementation details, and documentation must align with these principles and with `platform-master-strategy.md`.

---

## GitOps First

All system changes **must go through Git**:

- Configuration, code, and infrastructure are versioned in Git.
- Changes are applied only via:
  - Pull Requests,
  - CI pipelines,
  - CD scripts/pipelines (see `gitops-architecture.md`).
- Direct changes on the running VM (e.g. editing files under `/opt/platform` without Git) are not allowed except for emergency debugging, and must be followed by a Git change that restores consistency.

---

## Immutable Deployment

The platform uses **immutable containers**:

- No direct modification of running containers:
  - No `docker exec`-based hotfixes as permanent solutions.
  - No in-place package installation in running containers.
- Every change is delivered by:
  - Building a new container image,
  - Deploying it via CI/CD,
  - Rolling back by redeploying a previous image if needed.

Operational runbooks (e.g. incident response) must reference **deploy/rollback scripts or pipelines**, not ad-hoc container patching.

---

## Observability-Driven Operation

“No monitoring = no system”:

- All services must emit:
  - Metrics (latency, traffic, errors, saturation where applicable),
  - Logs that can be searched centrally.
- The platform must provide:
  - Dashboards for key flows,
  - Alerts for critical failures and saturation conditions.
- Changes are only considered **done** when:
  - They have adequate visibility in the observability stack,
  - They do not silently degrade existing SLIs (see `sli-slo-sla.md`).

---

## Automation First

Manual work should be:

- Eliminated where reasonable, or
- Turned into scripts and integrated into pipelines.

Concretely:

- Runbooks should point to **scripts in `/opt/platform/scripts`** or CI/CD jobs, not long shell command sequences.
- Common operations (deploy, rollback, backup, restore, log inspection helpers) must be automated and documented.

---

## Resource Efficiency

The platform is designed for a **resource-constrained environment**:

- Runs entirely on a **single VM with 6GB RAM**.
- Prefers:
  - Lightweight components,
  - Shared infrastructure (single PostgreSQL, single monitoring stack),
  - Bounded background jobs.
- Avoids:
  - Heavy service meshes,
  - Per-service databases by default,
  - Always-on components without a clear need.

Every new component must justify its memory and CPU usage in the context of the global budget (see `platform-constraints.md` and `runtime-environment.md`).

---

## Constraint-Driven Architecture

The system is intentionally constrained to:

- A single VM,
- 6GB RAM,
- No horizontal scaling.

Every architectural and technology choice must:

- Optimize memory footprint and idle CPU usage,
- Minimize operational complexity,
- Be aligned with the constraints defined in `platform-master-strategy.md`.

If a desired feature cannot be achieved within these constraints, this must be made explicit in the documentation as a trade-off or a future evolution path, not silently implemented in violation of the constraints.



==================================================
SOURCE_PATH: ./docs-devops/02-system-architecture/data-flow.md
==================================================
# Data Flow

This document describes the main flows through the platform: CI, runtime traffic, and monitoring.

---

## CI Flow

```text
Developer / AI
      │
      ▼
     Git (push)
      │
      ▼
  CI Pipeline
      │
      ▼
 Build container image
      │
      ▼
  Push artifact (image registry)
      │
      ▼
   CD deploys new version
```

For more detail, see `ci-architecture.md` and `gitops-architecture.md`.

---

## Runtime Flow

```text
Client Request
      │
      ▼
 [Reverse Proxy]
      │
      ▼
 [Application Service]
      │
      ▼
 [PostgreSQL DB]
      │
      ▼
   Response
```

---

## Monitoring Flow

```text
Services
   ├─► Metrics ─► Prometheus ─► Dashboards (Grafana) ─► Alerts
   └─► Logs    ─► Loki       ─► Logs UI (Grafana)
```

These flows ensure that code changes, runtime behaviour, and observability remain consistent with the platform strategy.



==================================================
SOURCE_PATH: ./docs-devops/02-system-architecture/high-level-architecture.md
==================================================
# High Level Architecture

This document provides a high-level view of the Nano DevOps Platform, showing how traffic, CI/CD, and observability components interact.

---

## 1. Runtime Request Flow

```text
Internet User
     │
     ▼
 [Reverse Proxy (Traefik)]
     │
     ▼
 [Application Services]
     │
     ▼
 [Database (PostgreSQL)]
```

All external traffic enters through the reverse proxy, which routes requests to application services that use a shared PostgreSQL database.

---

## 2. CI/CD Flow

```text
Developer / AI
     │
     ▼
     Git
     │
     ▼
 [CI Pipeline]
     │
     ▼
 [Image Registry]
     │
     ▼
 [CD Layer]
     │
     ▼
 [Runtime (Docker on single-node VM)]
```

For details, see `ci-architecture.md`, `cd-strategy.md`, and `gitops-architecture.md`.

---

## 3. Observability Flow

```text
Services
   ├─► Metrics ─► Prometheus ─► Grafana ─► Alerts
   └─► Logs    ─► Loki       ─► Grafana (logs)
```

Observability is mandatory for all platform components; see `monitoring-architecture.md` and `sli-slo-sla.md` for more information.



==================================================
SOURCE_PATH: ./docs-devops/02-system-architecture/logical-architecture.md
==================================================
# Logical Architecture

This document describes the logical layers of the Nano DevOps Platform.

---

## Layers

```text
         ┌───────────────────────────┐
         │       Edge Layer         │
         │   (Traefik reverse proxy)│
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │      Application Layer   │
         │     (Business services)  │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │        Data Layer        │
         │      (PostgreSQL DB)     │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │       Compute Layer      │
         │      (Docker runtime)    │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │        CI/CD Layer       │
         │   (Pipelines & scripts)  │
         └────────────┬─────────────┘
                      │
         ┌────────────▼─────────────┐
         │    Observability Layer   │
         │ (Prometheus / Grafana /  │
         │          Loki)           │
         └──────────────────────────┘
```

### Edge Layer
Traefik reverse proxy.

### Compute Layer
Docker runtime on a single-node VM.

### Application Layer
Business services (stateless where possible).

### Data Layer
PostgreSQL as the main persistent data store.

### CI/CD Layer
Pipeline automation and deployment scripts that implement GitOps.

### Observability Layer
Metrics, logs, and alerting integrated with all other layers.



==================================================
SOURCE_PATH: ./docs-devops/03-tech-stack/tech-stack-decision.md
==================================================
# Tech Stack Decisions

## Why Docker instead of Kubernetes

- Lower resource usage
- Simpler operation
- Phù hợp single-node

## Why Traefik

- Dynamic configuration
- Native Docker integration
- Lightweight

## Why Self-hosted

- Full control
- Cost optimization
- Production-like learning environment

All tools must satisfy:

- Memory footprint < 300MB (steady state)
- Low idle CPU
- Single-node compatible


==================================================
SOURCE_PATH: ./docs-devops/03-tech-stack/tech-stack.md
==================================================
# Tech Stack

| Layer | Tool | Purpose |
|------|------|---------|
Edge | Traefik | Routing & SSL |
Runtime | Docker | Container execution |
CI | Git-based pipeline | Build & test |
CD | Scripted deployment | Release management |
Database | PostgreSQL | Persistent data |
Monitoring | Prometheus | Metrics |
Visualization | Grafana | Dashboard |
Logging | Loki | Log aggregation |
Backup | Cron + script | Data protection |


==================================================
SOURCE_PATH: ./docs-devops/04-environment-and-infrastructure/filesystem-layout.md
==================================================
# Filesystem Layout

/opt/platform
  ├── apps
  ├── data
  ├── monitoring
  ├── ci
  └── scripts


==================================================
SOURCE_PATH: ./docs-devops/04-environment-and-infrastructure/runtime-environment.md
==================================================
# Runtime Environment

## Host Machine

Windows + VMware

## VM

Alpine Linux

## Resource Allocation

RAM: 6GB (zram enabled)

## Network Model

Bridged networking

## Storage Layout

/opt/platform

## Resource Budget

Total RAM: 6GB

Allocation Strategy:

Reverse proxy: 200MB
CI runner: 1GB (burst)
Application: 1.5GB
Database: 1.5GB
Monitoring stack: 1GB
Buffer: 800MB

### Text Diagram: Resource Allocation

```text
6GB Total RAM

┌───────────────────────────────────────────┐
│ Reverse proxy        ≈ 200MB             │
├───────────────────────────────────────────┤
│ CI runner (burst)    ≈ 1GB               │
├───────────────────────────────────────────┤
│ Application services ≈ 1.5GB             │
├───────────────────────────────────────────┤
│ PostgreSQL DB        ≈ 1.5GB             │
├───────────────────────────────────────────┤
│ Monitoring stack     ≈ 1GB               │
├───────────────────────────────────────────┤
│ Buffer (headroom)    ≈ 800MB             │
└───────────────────────────────────────────┘
```

### Per-Service Considerations

- New always-on services should target **tens of MB**, not hundreds.
- Background/batch jobs should:
  - Run for limited durations,
  - Release memory after completion.
- If projected usage would exceed these budgets, the change must be redesigned or explicitly approved as a constraint change.


==================================================
SOURCE_PATH: ./docs-devops/05-ci-cd/cd-strategy.md
==================================================
# CD Strategy

## Deployment Steps

1. Pull new image
2. Health check
3. Switch traffic
4. Remove old version

## Rollback

Re-deploy previous image


==================================================
SOURCE_PATH: ./docs-devops/05-ci-cd/ci-architecture.md
==================================================
# CI Architecture

## Stages

- Lint
- Build
- Test
- Package
- Security & law checks

The **security & law checks** stage must at minimum include:

- Static Application Security Testing (SAST)
- Dependency / vulnerability scanning
- Secret detection
- Platform law checks (small batch, trunk-based, unit tests, SLO/telemetry presence) as defined in `ai-context/platform-laws.yaml` và `ai-context/ci-enforcement/law-checks.yaml`.

## Artifact

Container image


==================================================
SOURCE_PATH: ./docs-devops/05-ci-cd/gitops-architecture.md
==================================================
# GitOps Architecture

This document specifies how **Git** controls the Nano DevOps Platform, and how changes flow from source control to the single-node runtime in a way that respects **immutable deployment** and **automation-first** principles.

---

## 1. Repositories and Scope

- **Platform repository (this repo)**
  - Contains:
    - Application service definitions and Docker Compose files
    - CI pipeline configuration
    - CD scripts and configuration
    - Monitoring configuration
    - Documentation (`/docs`)
  - Acts as the **single source of truth** for platform state.

---

## 2. Environments and Branching

- **Main branch**
  - Represents the desired state of the **single production-like environment**.
  - Only updated through Pull Requests (PRs) with review.
- **Feature branches**
  - Used for development and experimentation.
  - Must target `main` via PR.

Even in a single-node setup, **all changes** must go through this PR flow.

---

## 3. Change Flow (Git → CI → CD → Runtime)

High-level GitOps pipeline:

```text
Developer / AI
    │  (1) Commit & PR
    ▼
     Git (feature branch)
    │  (2) CI: lint → build → test → package → security & law checks
    ▼
  Image Registry (versioned images)
    │  (3) Merge to main (after review & green CI)
    ▼
   CD Scripts / Pipelines
    │  (4) Deploy: pull image → health check → switch traffic
    ▼
 Single-node Docker Runtime
```

- **Step 1 – Commit & PR**
  - All platform changes are committed to Git and proposed via PR.
  - No direct edits to the live VM are allowed.
- **Step 2 – CI**
  - Defined in `ci-architecture.md`.
  - Produces an immutable container image as the deployment artifact.
  - Enforces platform laws for:
    - Small batch changes và trunk-based development,
    - Presence of unit tests,
    - SLO/telemetry configuration,
    - Security scans (SAST, dependency scan, secret detection).
- **Step 3 – Merge to `main`**
  - Requires:
    - At least one human review (for human-driven changes).
    - Green CI (bao gồm security & law checks).
- **Step 4 – CD**
  - Implemented by scripts/pipelines in the platform repo.
  - Uses rolling update with health checks (see `deployment-pattern.md`).

---

## 4. Configuration Management

- **Application configuration**
  - Stored in:
    - Docker Compose files,
    - Per-service configuration files within the repo.
  - Externalized from container images (see `engineering-philosophy.md`).
- **Secrets**
  - Never committed in clear text.
  - Passed via environment variables or external secret stores.
- **Runtime configuration**
  - Any change that affects runtime behaviour must be:
    - Represented in Git,
    - Deployed via CI/CD.

There are **no "manual only" configuration paths**.

---

## 5. Rollback via GitOps

Rollback is performed by reverting Git state and redeploying:

```text
Problem detected
    │
    ▼
  Git revert / rollback commit
    │
    ▼
 Re-run CI (if needed) or reuse existing image
    │
    ▼
   CD re-deploys previous image
```

- Platform never patches containers in place.
- Operational docs (e.g. `incident-response.md`) must point to:
  - `rollback` scripts or CD pipeline jobs,
  - Not to ad-hoc manual shell commands.

---

## 6. Responsibilities and Ownership

- **Developers**
  - Propose changes via PR.
  - Keep service-level docs and configs consistent.
- **Platform maintainers**
  - Own CI/CD configuration, GitOps workflows, and core runtime definitions.
  - Guardrails:
    - Enforce non-root containers,
    - Enforce Git-only changes to runtime.
- **AI agents**
  - May author PRs that follow:
    - This GitOps architecture,
    - `ai-coding-guidelines.md`,
    - `system-context.md`.
  - Must never bypass Git or manipulate runtime state directly.

---

## 7. Text Diagram: End-to-End GitOps Loop

```text
          ┌────────────────────┐
          │   Developer / AI   │
          └─────────┬──────────┘
                    │  (1) PR with code+config changes
                    ▼
            ┌──────────────┐
            │     Git      │
            │ (feature br) │
            └──────┬───────┘
                   │  (2) CI: build & test
                   ▼
         ┌──────────────────────┐
         │   Image Registry     │
         │ (versioned images)   │
         └─────────┬────────────┘
                   │  (3) Merge to main
                   ▼
           ┌────────────────┐
           │    CD Layer    │
           │ (scripts/pipes)│
           └────────┬───────┘
                    │  (4) Deploy/rollback
                    ▼
         ┌──────────────────────┐
         │  Docker Runtime VM   │
         └──────────────────────┘
```




==================================================
SOURCE_PATH: ./docs-devops/06-deployment-strategy/deployment-pattern.md
==================================================
# Deployment Pattern

Rolling update with health check.

## Goals

- Zero downtime
- Fast rollback


==================================================
SOURCE_PATH: ./docs-devops/07-observability/monitoring-architecture.md
==================================================
# Monitoring Architecture

This document describes how metrics, logs, and alerts are implemented for the Nano DevOps Platform.

---

## 1. Components

- **Metrics**
  - Prometheus
- **Visualization**
  - Grafana
- **Logs**
  - Loki
- **Alerting**
  - Prometheus alert rules and/or Grafana alerting
 - **Traces (future-ready)**
   - Lightweight tracing or span export can be added for critical flows when resources allow

All application and platform services must integrate with this stack.

---

## 2. Data Flows (Text Diagram)

```text
Metrics Flow:

 [Services] ──► [Prometheus] ──► [Grafana Dashboards] ──► [Alerts]

Logging Flow:

 [Services] ──► [Loki] ──► [Grafana Log Explorer]

Resource Monitoring:

 [Node / Docker] ──► [Prometheus node/container exporters] ──► [Grafana]
```

---

## 3. What We Monitor

- **Platform health**
  - Service up/down status (Traefik, app services, PostgreSQL, monitoring stack itself).
  - Node-level metrics: CPU, memory, disk usage.
- **Application health**
  - Request rate, error rate, latency.
  - Business-specific metrics where defined.
- **Deployment health**
  - Deployment success/failure counts.
  - Rollback events.

Alerts should be defined for, at minimum:

- Service down (critical services),
- High CPU (sustained),
- High memory (sustained),
- Disk nearly full,
- SLO/SLA breaches (see `sli-slo-sla.md`).

---

## 4. Resource-Aware Observability

Given the 6GB RAM constraint:

- **Retention**
  - Keep metrics and logs only for as long as is useful for debugging and SLO tracking.
  - Use short to moderate retention windows and, if needed, sampling or label restrictions.
- **Scrape intervals**
  - Balance freshness with overhead (e.g. 15–30s for most services).
- **Dashboards**
  - Focus on a small set of **high-value** dashboards:
    - Platform overview,
    - Per-critical-service dashboard,
    - Resource (CPU/RAM/disk) dashboard.

If resource pressure arises, prefer to **tune retention and scrape settings** before adding new heavy observability components.

Even though `platform-laws` yêu cầu **logs, metrics, traces**, bản Nano này ưu tiên logs + metrics để phù hợp constraint 6GB RAM; traces được coi là tùy chọn, tập trung trước cho các luồng thực sự quan trọng nếu được bật.



==================================================
SOURCE_PATH: ./docs-devops/07-observability/sli-slo-sla.md
==================================================
# SLI / SLO / SLA

This document defines basic Service Level Indicators (SLIs) and Service Level Objectives (SLOs) for the Nano DevOps Platform, consistent with the **observability-first** principle.

---

## 1. Core SLIs

- **Platform availability**
  - SLI: Percentage of successful HTTP requests (2xx/3xx) at the edge (Traefik).
  - SLO: **99%** over a rolling 30-day period.
- **Deployment success rate**
  - SLI: Ratio of successful deployments to total deployments over a period.
  - SLO: **> 95%** successful deployments per 30 days.
- **Service latency**
  - SLI: P95 response time for key APIs.
  - SLO: P95 < 500ms for normal load for critical endpoints.
- **Error rate**
  - SLI: Percentage of 5xx responses for key services.
  - SLO: Error rate < 1% for normal operation.

---

## 2. Alerting Guidelines

Alerts should fire when SLOs are at risk, not for every minor fluctuation.

- **Availability / Error rate**
  - Trigger an alert if:
    - Error rate > 5% for 5 minutes, or
    - Projected SLO burn rate indicates a violation within 1 day.
- **Latency**
  - Trigger an alert if:
    - P95 latency > 1s for 10 minutes on critical endpoints.
- **Deployment failures**
  - Alert when:
    - A deployment fails and rollback is triggered,
    - Deployment success rate drops below the objective over a rolling window.

These alerts integrate with `incident-response.md`, which describes how to diagnose and remediate issues using scripts and rollback mechanisms.

---

## 3. Text Diagram: SLO Flow

```text
Traffic ─► Metrics (Prometheus)
             │
             ▼
         SLI calculations
             │
             ▼
      Compare to SLO targets
             │
             ├─► Within bounds  ─► Dashboards only
             │
             └─► Breach / at risk ─► Alerts ─► Incident Response
```



==================================================
SOURCE_PATH: ./docs-devops/08-security/security-baseline.md
==================================================
# Security Baseline

- Non-root container
- Secrets via environment
- Internal network isolation
- Limited exposed ports


==================================================
SOURCE_PATH: ./docs-devops/09-disaster-recovery/backup-restore-strategy.md
==================================================
# Backup & Restore Strategy

This document describes how the platform performs backups and restores in a way that is **automated**, **script-driven**, and aligned with the single-node resource constraints.

---

## 1. Objectives

- **RTO** (Recovery Time Objective): < 1 hour  
- **RPO** (Recovery Point Objective): < 24 hours

These targets apply to the primary PostgreSQL database and critical application data.

---

## 2. Backup Process

Backups are performed automatically via scripts scheduled on the VM.

```text
Cron scheduler
    ↓
 backup-db.sh
    ↓
 Database dump + compression
    ↓
 Store in /opt/platform/data/backup (or configured backup location)
```

- **Frequency**
  - At least once per day.
- **Scope**
  - PostgreSQL database (full logical dump or physical backup as configured).
- **Location**
  - Stored on local disk and, optionally, synced to external storage (if configured).
- **Implementation**
  - Script example: `backup-db.sh` in `/opt/platform/scripts`.

Backups must be lightweight enough to fit within the storage and memory constraints of the single-node environment.

---

## 3. Restore Process

Restores are performed by **running a restore script**; no manual ad-hoc SQL is required for standard scenarios.

```text
Select backup snapshot
    ↓
 stop-apps.sh (optional: stop or drain traffic)
    ↓
 restore-db.sh <backup-id>
    ↓
 start-apps.sh (or deploy scripts)
    ↓
 Verify application & data
```

- **Script usage**
  - `restore-db.sh <backup-id>`:
    - Stops or isolates the database as needed.
    - Restores the selected backup.
    - Logs progress and results.
- **Post-restore validation**
  - Verify:
    - Applications can connect to the DB,
    - Critical workflows function correctly,
    - Monitoring shows normal behaviour.

Any change in restore procedures must be reflected in this document and in the scripts under `/opt/platform/scripts`.

---

## 4. Testing and Verification

To ensure RTO and RPO targets remain realistic:

- Periodically run **restore drills** in a controlled environment:
  - Measure time from “backup selection” to “service healthy again”.
  - Check that data aligns with expected point-in-time (RPO).
- Document test results and adjust:
  - Backup frequency,
  - Script implementation,
  - Storage allocation,
as needed.

---

## 5. Text Diagram: Backup & Restore Flows

```text
Backup Flow:

   [Cron] ──► [backup-db.sh] ──► [Compressed backup files]
                                      │
                                      ▼
                           [Local / External Storage]

Restore Flow:

  [Operator]
      │
      ▼
 [Choose backup]
      │
      ▼
 [restore-db.sh] ──► [PostgreSQL restored]
      │
      ▼
 [Apps (re)started via deploy scripts]
```



==================================================
SOURCE_PATH: ./docs-devops/10-runbook/incident-response.md
==================================================
# Incident Response

This runbook describes how to handle common incidents using **automated scripts and GitOps-based rollback**, consistent with immutable deployment and automation-first principles.

---

## 1. Overview Text Diagram

```text
Alert / User Report
        ↓
   Triage & Identify
        ↓
   Use scripts / CI jobs
        ↓
 Verify & close incident
        ↓
    Create postmortem (if needed)
```

All remediation should be performed via:

- Scripts in `/opt/platform/scripts`, or
- CI/CD jobs defined in the platform repo,

not by manually patching running containers.

---

## 2. Service Down

### 2.1 Diagnosis

- Check monitoring dashboards (see `monitoring-architecture.md`):
  - Confirm whether only one service is down or multiple.
- Check logs via Loki for the affected service.
- Confirm the last deployment status in CI/CD.

### 2.2 Remediation (Immutable and Automated)

1. **Attempt automated redeploy**
   - Run the service deployment script (example):
     - `deploy-service.sh <service-name>`
   - This will:
     - Pull the current image for the service,
     - Run health checks,
     - Switch traffic if healthy.
2. **Rollback if redeploy fails**
   - Trigger the rollback script (example):
     - `rollback-service.sh <service-name>`
   - Or trigger the corresponding CD pipeline job that re-deploys the previous known-good image.
3. **Escalate**
   - If both redeploy and rollback fail:
     - Capture logs and metrics snapshots,
     - Escalate to platform maintainers with detailed context.

At no point should you permanently fix issues by logging into containers and changing code or configuration in place.

---

## 3. Database Full

### 3.1 Diagnosis

- Confirm alert details:
  - Disk usage on the data volume,
  - Database size and largest tables.
- Use monitoring tools to identify growth trends.

### 3.2 Remediation (Scripted)

1. **Run data cleanup script**
   - Use a documented script, for example:
     - `cleanup-db-data.sh`
   - The script should:
     - Remove or archive old, non-critical data according to policy,
     - Log all actions taken.
2. **If volume extension is required**
   - Follow the documented storage expansion procedure (outside the scope of this runbook), then:
     - Update any relevant configuration in Git if mount points or sizes need to be reflected there.
3. **Verify**
   - Confirm free space is back within safe thresholds.
   - Ensure alerts are cleared and performance is normal.

Manual ad-hoc deletion of data from within the database without a script or well-defined SQL migration should be avoided. Any structural or policy changes must be captured in Git.



==================================================
SOURCE_PATH: ./docs-devops/11-development-guide/contribution-guide.md
==================================================
# Contribution Guide

This document describes how to safely contribute changes to the Nano DevOps Platform while respecting **GitOps**, **immutable deployment**, and the **6GB single-node constraint**.

---

## Rules

- **All changes via Pull Request (PR)**
  - No direct pushes to `main`.
  - All PRs must pass CI before merge.
- **Small batch, trunk-based**
  - Ưu tiên PR nhỏ, tập trung, với tổng số dòng thay đổi khoảng **≤ 300 lines** (theo `delivery.small_batch.max_lines`).
  - Feature branch nên sống **< 24 giờ** trước khi merge vào `main` (theo `delivery.trunk_based.max_branch_lifetime_hours`). 
- **Update documentation**
  - Any behavioural or architectural change must be reflected in `/docs`.
  - New services must include architecture notes and, where relevant, runbook entries.
- **Follow folder structure**
  - Place application services, infra, and scripts in the appropriate directories as described in `system-context.md` and `filesystem-layout.md`.

---

## GitOps Workflow (Contributor View)

```text
Create small, focused branch (lifetime < 24h)
  ↓
Implement change (code + config + docs), keep diff ≈ ≤ 300 lines
  ↓
Push branch + open PR
  ↓
CI: lint → build → test → package → security & law checks
  ↓
Review & iterate
  ↓
Merge to main
  ↓
CD: deploy via scripts/pipelines
```

- Contributors must not modify runtime state on the VM by hand; if an emergency fix is performed, it must be:
  - Captured in a Git change,
  - Deployed via the normal pipeline as soon as possible.
  - Follow-up PRs vẫn phải tuân thủ luật small batch và trunk-based ở trên.

---

## Expectations for Changes

- **Respect constraints**
  - Any new component must fit within the 6GB RAM budget.
  - Avoid adding heavy dependencies without clear justification.
- **Keep the system observable**
  - New services should expose metrics and logs that integrate with the existing monitoring stack.
- **Keep operations automated**
  - Repetitive steps should be implemented as scripts or CI/CD jobs, not copied shell commands.

---

## AI-Assisted Contributions

- AI tools (e.g. Cursor) may help:
  - Generate code and configuration,
  - Draft documentation,
  - Propose CI/CD updates.
- They must follow:
  - `ai-coding-guidelines.md`,
  - `system-context.md`,
  - `gitops-architecture.md`.

Human reviewers remain responsible for ensuring that AI-generated changes comply with the platform strategy and constraints.



==================================================
SOURCE_PATH: ./docs-devops/11-development-guide/local-development.md
==================================================
# Local Development

This guide helps a new developer run the platform locally, make a simple change, and understand how it flows through CI/CD.

---

## 1. Prerequisites

- Git installed.
- Docker and Docker Compose installed.
- Access to this repository.

---

## 2. Start the Platform Locally

1. **Clone the repository**
   - `git clone <repo-url>`
2. **Enter the project directory**
   - `cd <repo-root>`
3. **Start services**
   - `docker compose up` (or the equivalent provided in this repo).
4. **Access the platform**
   - Open the reverse proxy entry point (e.g. `http://localhost:<port>`).

Text diagram:

```text
Developer machine
    │
    ├─► git clone
    ├─► docker compose up
    └─► browser ─► localhost (reverse proxy)
```

---

## 3. Make a Simple Change

1. Create a new branch from `main`.
2. Modify a small part of an application service (e.g. a health endpoint).
3. Run tests locally if available.
4. Commit your changes with a clear message.

---

## 4. From Local to CI/CD

1. Push your branch to the remote repository.
2. Open a Pull Request (PR) against `main`.
3. CI will run:
   - Lint,
   - Build,
   - Test,
   - Package (see `ci-architecture.md`).
4. After review and green CI, merge the PR.
5. CD will deploy the new version using rolling update and health checks (see `gitops-architecture.md` and `deployment-pattern.md`).

```text
Local change
    ↓
   Git (branch)
    ↓
    PR
    ↓
   CI
    ↓
   Main
    ↓
   CD
    ↓
 Runtime VM
```

---

## 5. Observability During Development

- Use Grafana dashboards to see metrics for your services.
- Use Loki queries to inspect logs.
- After a deployment, confirm that:
  - Health checks are passing,
  - Error rates remain low,
  - Latency stays within SLO targets (see `sli-slo-sla.md`). 



==================================================
SOURCE_PATH: ./docs-devops/99-appendix/glossary.md
==================================================
# Glossary

Artifact: build output  
SLI: service level indicator  
SLO: target reliability  


==================================================
SOURCE_PATH: ./docs-devops/get_final_devops_context.sh
==================================================






==================================================
SOURCE_PATH: ./docs-ai-context/get_final_ai_context.sh
==================================================



==================================================
SOURCE_PATH: ./docs-ai-context/golden-path/environment.yaml
==================================================
environments:
  - dev
  - staging
  - prod

parity: required
config_externalized: true


==================================================
SOURCE_PATH: ./docs-ai-context/golden-path/pipeline.yaml
==================================================
stages:
  - validate_laws
  - unit_test
  - build
  - security_scan
  - deploy

policies:
  fail_on_missing_test: true
  fail_on_large_change: true


==================================================
SOURCE_PATH: ./docs-ai-context/golden-path/service.yaml
==================================================
service:
  structure:
    layers:
      - domain
      - application
      - infrastructure

  runtime:
    healthcheck: required
    resource_limits: required

  observability:
    logs: structured
    metrics: enabled
    traces: enabled

  reliability:
    slo: required


==================================================
SOURCE_PATH: ./docs-ai-context/law-context-mapping.yaml
==================================================
foundation:
  - delivery.small_batch
  - delivery.trunk_based

service_template:
  - reliability.slo_required
  - observability.telemetry_required
  - architecture.stateless_service

ci_cd:
  - delivery.testability
  - security.secure_pipeline

runtime:
  - infra.immutable

observability:
  - reliability.error_budget_policy


==================================================
SOURCE_PATH: ./docs-ai-context/platform-laws.yaml
==================================================
delivery:
  small_batch:
    max_lines: 300

  trunk_based:
    max_branch_lifetime_hours: 24

  testability:
    unit_test_required: true

reliability:
  slo_required: true
  error_budget_policy: enforced

architecture:
  stateless_service: true
  explicit_data_flow: true

observability:
  telemetry_required:
    - logs
    - metrics
    - traces

security:
  secure_pipeline:
    - sast
    - dependency_scan
    - secret_scan

infra:
  immutable: true
  idempotent: true


==================================================
SOURCE_PATH: ./docs-ai-context/platform-vision.md
==================================================
# PLATFORM VISION

The platform is treated as a product.

Primary users: application developers  
Goal: reduce cognitive load and enable fast, safe delivery.

## Core Principles

- Self-service over manual ops
- Golden path is the default
- Everything measurable
- Small batch changes
- Trunk-based development
- Reliability as a feature

## Delivery Performance Targets (DORA)

Deployment frequency: daily  
Lead time for change: < 1 day  
MTTR: < 1 hour  
Change failure rate: < 15%

## SRE Runtime Targets

Every service must define:
- SLI
- SLO
- Error budget

Toil < 30%


==================================================
SOURCE_PATH: ./docs-ai-context/slo/error-budget-policy.yaml
==================================================
error_budget:

  burn_rate_threshold: 2

actions_on_exhaustion:
  - freeze_release
  - focus_on_reliability


==================================================
SOURCE_PATH: ./docs-ai-context/slo/slo-template.yaml
==================================================
slo:
  availability: 99.9
  latency_p95_ms: 300
  error_rate: 1%


==================================================
SOURCE_PATH: ./docs-ai-context/system-context.md
==================================================
# AI System Context

This document defines the minimal context an AI agent (e.g. Cursor) needs to safely propose and implement changes on the Nano DevOps Platform while respecting the **single-node 6GB constraint**, **GitOps**, and **immutable deployment** principles defined in `platform-master-strategy.md`.

---

## 1. Repository and Filesystem Overview

### 1.1 Repositories

- **Platform repo (this repo)**:  
  - Contains:
    - Infrastructure as code (Docker / docker-compose, runtime scripts)
    - Platform services definitions
    - CI/CD definitions
    - Documentation (`/docs`)
  - **Git is the only source of truth** for platform state.

### 1.2 Filesystem Layout on VM

See `filesystem-layout.md` for details. High-level:

```text
/opt/platform
  ├── apps            # Application services (per-service folders)
  ├── data            # Persistent data (e.g. PostgreSQL volumes)
  ├── monitoring      # Prometheus / Grafana / Loki config & data
  ├── ci              # CI/CD runner and related scripts
  └── scripts         # Operational automation (deploy, backup, restore, etc.)
```

AI agents should **treat this structure as stable** and only modify files where explicitly allowed below.

---

## 2. Naming Conventions

- **Services**
  - Lowercase, hyphen-separated, short but descriptive.  
    - Examples: `user-service`, `billing-api`, `reporting-worker`.
- **Docker Compose service names**
  - Match application service names where possible, with suffixes for infrastructure when needed.  
    - Examples: `user-service`, `platform-postgres`, `platform-prometheus`.
- **Monitoring artifacts**
  - Prometheus job names follow `layer-service` style.  
    - Example: `app-user-service`, `infra-traefik`.
- **Scripts**
  - Use verb-noun form and be explicit about scope.  
    - Examples: `deploy-service.sh`, `rollback-service.sh`, `backup-db.sh`, `restore-db.sh`.

---

## 3. Deployment Flow (GitOps and Immutable)

The only safe way for AI to change the running system is through **Git → CI → CD → Runtime**.

```text
Developer / AI
    ↓ (1) Git commit + PR
Git repository
    ↓ (2) CI pipeline (lint → build → test → package)
Container registry
    ↓ (3) CD pipeline (pull image → health check → switch traffic)
Runtime (Docker on single-node VM)
```

- **Step 1 – Git change**
  - All configuration and code changes are committed to Git.
  - No direct modification of files on `/opt/platform` by hand.
- **Step 2 – CI**
  - Builds container images and runs tests.
  - Produces versioned artifacts (immutable images).
- **Step 3 – CD**
  - Pulls the new image, performs health checks, and switches traffic using rolling update (see `deployment-pattern.md`).
  - Old versions are removed only after successful verification.

AI proposals **must not** bypass this flow.

---

## 4. Service Dependency Map (Conceptual)

For full details see `high-level-architecture.md` and `logical-architecture.md`. Quick textual view:

```text
          Internet User
                │
                ▼
          [Traefik Edge]
                │
                ▼
         [App Services]*  ────►  [PostgreSQL]
                │
                └────────►  [Monitoring Exporters]

CI/CD:
Developer / AI
    │
    ▼
   [Git]
    │
    ▼
 [CI Pipeline] ──► [Image Registry] ──► [CD Scripts] ──► [Docker Runtime]

Observability:
Services ─► [Prometheus] ─► [Grafana]
Logs    ─► [Loki]
Alerts  ─► Alert rules (Prometheus / Grafana)
```

- All app services:
  - Receive traffic only via the reverse proxy.
  - Use **shared PostgreSQL** (no per-service DB by default).
  - Export metrics and logs into the shared monitoring stack.

---

## 5. Allowed Operations for AI

AI agents may:

- **Create or modify application services** under the designated app/service configuration areas:
  - Add/update service definitions in the appropriate Docker Compose file(s) **for application layer only**.
  - Add/update app code within `/opt/platform/apps/<service-name>` (via Git).
- **Extend observability for services**:
  - Add Prometheus scrape configs for new services.
  - Add/update dashboards for new services.
- **Update documentation**:
  - Extend `docs` to describe new services, flows, and runbooks.
- **Modify CI config for new services**:
  - Add jobs/stages so new services are built, tested, and packaged consistently with existing ones.

All changes must **respect resource constraints** and **follow GitOps**.

---

## 6. Forbidden Actions for AI

The following are strictly **forbidden** for AI agents:

- **Core runtime and infrastructure**
  - Do not modify:
    - Core Docker runtime configuration (e.g. base Docker daemon settings).
    - Core infrastructure compose/services for:
      - Traefik
      - PostgreSQL
      - Prometheus / Grafana / Loki
      - CI runner
  - Do not change network topology (ports, network modes) for core components.
- **Resource model violations**
  - Do not introduce:
    - New always-on services that would obviously exceed the **6GB RAM** budget.
    - Per-service databases by default (see `ai-coding-guidelines.md`).
    - Heavy sidecar patterns that duplicate functionality of existing shared infrastructure.
- **Bypassing GitOps**
  - Do not:
    - Directly edit files on `/opt/platform` outside of Git workflows.
    - Suggest manual `docker exec` or in-container changes as permanent fixes.
    - Apply ad-hoc configuration changes that are not represented in Git.
- **Modifying platform design fundamentals**
  - Do not:
    - Introduce Kubernetes or service mesh.
    - Change the single-node / 6GB constraint assumptions.
    - Modify global security baselines (non-root containers, secrets handling, network isolation).

If a required change appears to need any of the above, the AI must instead:

- Document the limitation,
- Propose a **human-reviewed design change** as a separate architectural decision, not an automated code change.

---

## 7. Safe Change Checklist for AI

Before proposing or applying a change, an AI agent should verify:

1. **Constraint fit**
   - Estimated memory impact keeps total usage within the budget in `runtime-environment.md`.
   - No new long-running processes that significantly increase idle resource usage.
2. **GitOps compliance**
   - All modifications are represented as Git changes.
   - No instruction requires out-of-band manual edits on the VM.
3. **Immutable deployment**
   - Changes are rolled out via new container images, not by mutating running containers.
4. **Observability coverage**
   - New services expose metrics/logs consistent with existing standards.
   - Dashboards and alerts are updated if needed.
5. **Documentation**
   - Relevant docs in `/docs` are updated to reflect new behaviour and dependencies.

Only when all the above are satisfied should an AI proceed to suggest or orchestrate changes.



