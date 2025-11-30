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
