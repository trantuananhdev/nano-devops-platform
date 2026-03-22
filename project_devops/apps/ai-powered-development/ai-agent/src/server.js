const express = require("express");
const promClient = require("prom-client");
const { createOrchestrator } = require("./orchestrator");
const { createTenantMemory } = require("./storage/tenantMemory");

const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;

// Prometheus metrics
const register = new promClient.Registry();
promClient.collectDefaultMetrics({ register });

const httpRequestCounter = new promClient.Counter({
  name: "http_requests_total",
  help: "Total number of HTTP requests",
  labelNames: ["method", "route", "status_code"],
  registers: [register],
});

const app = express();
app.use(express.json({ limit: "2mb" }));

// Middleware for counting requests
app.use((req, res, next) => {
  res.on("finish", () => {
    const route = req.route ? req.route.path : req.path;
    httpRequestCounter.labels(req.method, route, res.statusCode).inc();
  });
  next();
});

function getTenantId(req) {
  return (req.body && req.body.tenantId) || (req.query && req.query.tenantId) || "demo";
}

function getRequesterFromHeaders(req) {
  const role = String(req.headers["x-user-role"] || "human").toLowerCase();
  const id = String(req.headers["x-user-id"] || "unknown-user");
  return { type: "human", role, id };
}

function requireAllowedRole(req, allowed) {
  const { role } = getRequesterFromHeaders(req);
  const normalized = String(role).toLowerCase().trim();
  if (!allowed.includes(normalized)) return { ok: false, error: "Forbidden role" };
  return { ok: true, role: normalized };
}

app.get("/healthz", (_req, res) => {
  res.json({ ok: true, service: "digital-fte-platform" });
});

app.get("/metrics", async (_req, res) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});

app.post("/v1/tasks", async (req, res) => {
  const tenantId = getTenantId(req);
  const { taskType, description, requester } = req.body || {};
  const roleCheck = requireAllowedRole(req, ["human", "admin", "agent-runner"]);
  if (!roleCheck.ok) return res.status(403).json({ error: roleCheck.error });
  const hdrRequester = getRequesterFromHeaders(req);

  if (!taskType || typeof taskType !== "string") {
    return res.status(400).json({ error: "Missing required field: taskType" });
  }
  if (!description || typeof description !== "string") {
    return res.status(400).json({ error: "Missing required field: description" });
  }

  try {
    const orchestrator = createOrchestrator({
      tenantMemory: createTenantMemory({ tenantId }),
    });

    const task = await orchestrator.createAndRunTask({
      taskType,
      description,
      requester:
        requester ||
        (roleCheck.role
          ? { type: "human", id: hdrRequester.id, role: roleCheck.role }
          : { type: "human", id: hdrRequester.id }),
    });

    res.status(201).json(task);
  } catch (err) {
    res.status(500).json({ error: String(err && err.message ? err.message : err) });
  }
});

app.get("/v1/tasks/:taskId", async (req, res) => {
  const tenantId = getTenantId(req);
  const taskId = req.params.taskId;
  try {
    const orchestrator = createOrchestrator({
      tenantMemory: createTenantMemory({ tenantId }),
    });
    const task = await orchestrator.getTask(taskId);
    if (!task) return res.status(404).json({ error: "Task not found" });
    return res.json(task);
  } catch (err) {
    return res.status(500).json({ error: String(err && err.message ? err.message : err) });
  }
});

app.post("/v1/tasks/:taskId/approve", async (req, res) => {
  const tenantId = getTenantId(req);
  const taskId = req.params.taskId;

  const roleCheck = requireAllowedRole(req, ["admin"]);
  if (!roleCheck.ok) return res.status(403).json({ error: roleCheck.error });

  const { decisionNotes } = req.body || {};
  const approver = String(req.headers["x-user-id"] || "admin");

  try {
    const tenantMemory = createTenantMemory({ tenantId });
    const task = tenantMemory.getTask(taskId);
    if (!task) return res.status(404).json({ error: "Task not found" });
    if (task.status !== "needs-human-review") {
      return res.status(400).json({ error: `Task is not in needs-human-review. Current: ${task.status}` });
    }

    const prevEvidence = task.verification && Array.isArray(task.verification.evidence) ? task.verification.evidence : [];
    task.humanApproval = {
      approvedBy: approver,
      decisionNotes: String(decisionNotes || ""),
      at: new Date().toISOString(),
    };

    // Human approval upgrades verification outcome for lifecycle/memory update.
    task.verification = {
      status: "pass",
      issues: [],
      evidence: [`Human approval by ${approver}: ${String(decisionNotes || "").slice(0, 240)}`].concat(prevEvidence),
    };

    task.status = "completed";
    task.updatedAt = new Date().toISOString();
    task.result = task.result || {};

    tenantMemory.updateAfterSession({ task });
    tenantMemory.upsertTask(task);
    tenantMemory.appendAudit({
      event: "task_human_approved",
      taskId: task.id,
      approvedBy: approver,
    });

    return res.json(task);
  } catch (err) {
    return res.status(500).json({ error: String(err && err.message ? err.message : err) });
  }
});

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`[ai-agent] Server listening on http://localhost:${PORT}`);
});

