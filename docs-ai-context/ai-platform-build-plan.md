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

