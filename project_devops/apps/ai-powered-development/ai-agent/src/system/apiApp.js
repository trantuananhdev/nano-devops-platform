const express = require("express");
const crypto = require("crypto");
const { requireAuth } = require("../auth/requireAuth");
const { signAccessToken } = require("../auth/jwt");
const { upsertTenantRepoCredential, findTenantByRepoFullName } = require("../adapters/db/githubRepoMappingRepo");
const { createQueuedTask, getTaskById, updateTaskProgress } = require("../adapters/db/taskRepo");
const { exportTaskReport } = require("../utils/reporter");

function safeEqual(a, b) {
  const aBuf = Buffer.from(String(a));
  const bBuf = Buffer.from(String(b));
  if (aBuf.length !== bBuf.length) return false;
  return crypto.timingSafeEqual(aBuf, bBuf);
}

function verifyGithubSignature(req) {
  const secret = process.env.GITHUB_WEBHOOK_SECRET;
  if (!secret) {
    const allowUnsigned = String(process.env.ALLOW_UNSIGNED_WEBHOOKS || "").toLowerCase() === "true";
    if (allowUnsigned) return true;
    return false;
  }

  const signatureHeader = req.headers["x-hub-signature-256"];
  if (!signatureHeader) return false;
  const parts = String(signatureHeader).split("=");
  if (parts.length !== 2) return false;
  const theirDigest = parts[1];

  // Use rawBody from the verify middleware to calculate HMAC correctly
  const body = req.rawBody || (Buffer.isBuffer(req.body) ? req.body : Buffer.from(JSON.stringify(req.body)));
  const hmac = crypto.createHmac("sha256", secret);
  hmac.update(body);
  const ourDigest = hmac.digest("hex");
  return safeEqual(ourDigest, theirDigest);
}

function createApiApp() {
  const app = express();
  
  // Support raw body for GitHub webhook verification
  app.use(express.json({
    limit: "2mb",
    verify: (req, res, buf) => {
      req.rawBody = buf;
    }
  }));

  app.get("/", (req, res) => {
    res.json({ name: "ai-agent", version: "1.0.0", status: "ok" });
  });

  // Mint token for MVP (admin-only via x-admin-api-key).
  app.post("/v1/auth/token", (req, res) => {
    const adminApiKey = req.headers["x-admin-api-key"];
    if (!adminApiKey || String(adminApiKey) !== String(process.env.ADMIN_API_KEY || "")) {
      return res.status(403).json({ error: "Forbidden" });
    }

    const { tenantId, userId, role } = req.body || {};
    if (!tenantId || !userId) return res.status(400).json({ error: "Missing tenantId/userId" });
    const resolvedRole = role || "admin";

    try {
      const token = signAccessToken({ tenantId, userId, role: resolvedRole });
      return res.json({ accessToken: token });
    } catch (err) {
      return res.status(500).json({ error: String(err && err.message ? err.message : err) });
    }
  });

  // Register GitHub repo credentials for a tenant.
  app.post("/v1/admin/github-repo", requireAuth({ roles: ["admin"] }), async (req, res) => {
    const tenantId = req.auth.tenantId;
    const { repoFullName, githubToken } = req.body || {};
    if (!repoFullName || !githubToken) return res.status(400).json({ error: "Missing repoFullName/githubToken" });

    try {
      await upsertTenantRepoCredential({ tenantId, repoFullName, githubToken });
      return res.json({ ok: true });
    } catch (err) {
      return res.status(500).json({ error: String(err && err.message ? err.message : err) });
    }
  });

  // GitHub Webhook (PR opened/synchronize -> queue a task).
  app.post(
    "/v1/webhooks/github",
    express.raw({ type: "application/json", limit: "2mb" }),
    async (req, res) => {
      try {
        const valid = verifyGithubSignature(req);
        if (!valid) return res.status(401).json({ error: "Invalid webhook signature" });

        const event = String(req.headers["x-github-event"] || "");
        const payload = JSON.parse(req.body.toString("utf8"));

        if (event !== "pull_request" || !payload.pull_request || !payload.repository) {
          return res.status(200).json({ ok: true, ignored: true });
        }

        const action = payload.action;
        const allowed = ["opened", "synchronize", "reopened", "edited"];
        if (!allowed.includes(action)) return res.status(200).json({ ok: true, ignored: true });

        const repoFullName = payload.repository.full_name;
        const prNumber = payload.pull_request.number;
        const prHeadSha = payload.pull_request.head && payload.pull_request.head.sha;

        if (!repoFullName || !prNumber || !prHeadSha) {
          return res.status(400).json({ error: "Missing webhook fields" });
        }

        const tenantRow = await findTenantByRepoFullName({ repoFullName });
        if (!tenantRow) {
          return res.status(200).json({ ok: true, ignored: true, reason: "repo not configured" });
        }

        const [repoOwner, repoName] = String(repoFullName).split("/");
        await createQueuedTask({
          tenantId: tenantRow.tenant_id,
          taskType: "github_pr_dev",
          repoOwner,
          repoName,
          prNumber,
          prHeadSha,
          maxAttempts: process.env.AGENT_MAX_ATTEMPTS ? Number(process.env.AGENT_MAX_ATTEMPTS) : 3,
        });

        return res.status(202).json({ ok: true });
      } catch (err) {
        return res.status(500).json({ error: String(err && err.message ? err.message : err) });
      }
    }
  );

  // AI-Powered Development: Ghost Installation (Simulate manual setup)
  app.get("/install", (req, res) => {
    const sensorImage = "nanodevops/agent-node:latest";
    const brainUrl = `http://${req.hostname}:3000/v1/incidents/report`;
    
    const script = `#!/bin/bash
echo "👻 Ghost Engineer Installation Script"
echo "--------------------------------------"
echo "Targeting Brain at: ${brainUrl}"

# 1. Run the Sensor
docker run -d \\
  --name ghost-sentinel \\
  --restart unless-stopped \\
  -v /var/run/docker.sock:/var/run/docker.sock:ro \\
  -e NODE_NAME=$(hostname) \\
  -e BRAIN_URL="${brainUrl}" \\
  ${sensorImage}

echo "✅ Ghost Sentinel is now haunting this node."
echo "🕵️ Monitoring managed containers..."
`;
    res.setHeader("Content-Type", "text/plain");
    return res.send(script);
  });

  // AI-Powered Development: Incident Reporting (The Sensor -> Brain endpoint)
  app.post("/v1/incidents/report", async (req, res) => {
    const payload = req.body;
    // eslint-disable-next-line no-console
    console.log("[ai-agent] 🚨 Incident on Node:", payload.nodeName, "| Container:", payload.containerName);

    try {
      // 1. Map incident to a repository (Senior Fix: Ensure labels are parsed correctly)
      const labels = payload.labels || {};
      const repoFullName = labels["com.github.repo"] || process.env.BOOTSTRAP_REPO_FULL_NAME || "unknown";
      const [repoOwner, repoName] = repoFullName.split("/");

      let tenantId = "tenant-1"; // Default for platform demo
      const tenantRow = await findTenantByRepoFullName({ repoFullName });
      if (tenantRow) tenantId = tenantRow.tenant_id;

      // 2. Create an 'incident_fix' task in the Ghost Workshop
      const task = await createQueuedTask({
        tenantId,
        taskType: "incident_fix",
        repoOwner: repoOwner || "unknown",
        repoName: repoName || payload.containerName || "unknown",
        prNumber: 0,
        prHeadSha: "live-incident-" + Date.now(),
        maxAttempts: 3,
      });

      // 3. Package context for the Brain
      await updateTaskProgress({
        tenantId,
        taskId: task.id,
        patch: {
          logs: payload.logs || "",
          metadata: {
            containerName: payload.containerName,
            containerID: payload.containerId,
            action: payload.action,
            exitCode: payload.exitCode,
            image: payload.image,
            sensorVersion: payload.sensorVersion,
            nodeName: payload.nodeName,
          },
        },
      });

      return res.status(202).json({
        ok: true,
        message: "Sentinel report received. Ghost Workshop is analyzing...",
        taskId: task.id,
      });
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("[ai-agent] Failed to process sentinel report:", err);
      return res.status(500).json({ error: "Failed to queue incident analysis" });
    }
  });

  // AI-Powered Development: Ghost Workshop Approval (Admin action)
  app.post("/v1/tasks/:taskId/approve", requireAuth({ roles: ["admin"] }), async (req, res) => {
    const tenantId = req.auth.tenantId;
    const taskId = req.params.taskId;

    try {
      const task = await getTaskById({ tenantId, taskId });
      if (!task) return res.status(404).json({ error: "Task not found" });

      if (task.status !== "completed" || !task.result) {
        return res.status(400).json({ error: "Task is not ready for approval (analysis must be complete)" });
      }

      // In a real system, this would trigger:
      // 1. GitHub PR creation (if it was an incident_fix)
      // 2. Or GitHub PR Merge (if it was a pr_dev task)
      // 3. Or direct deployment via CI/CD
      
      // For MVP, we simulate the "Ghost Engineer Action"
      console.log(`[ai-agent] ✅ Admin approved fix for task ${taskId}. Triggering Ghost Deployment...`);
      
      await updateTaskProgress({
        tenantId,
        taskId,
        patch: { 
          status: "approved", 
          progress_report: "Ghost Engineer is deploying the patch via CI/CD pipeline..." 
        }
      });

      return res.json({ 
        ok: true, 
        message: "Fix approved. Ghost Engineer is now deploying the solution to Production." 
      });
    } catch (err) {
      return res.status(500).json({ error: String(err) });
    }
  });

  // Get task status.
  app.get("/v1/tasks/:taskId", requireAuth({ roles: ["admin", "user"] }), async (req, res) => {
    const tenantId = req.auth.tenantId;
    const taskId = req.params.taskId;

    try {
      const task = await getTaskById({ tenantId, taskId });
      if (!task) return res.status(404).json({ error: "Task not found" });
      return res.json({ task });
    } catch (err) {
      return res.status(500).json({ error: String(err && err.message ? err.message : err) });
    }
  });

  // Get task report (markdown).
  app.get("/v1/tasks/:taskId/report", requireAuth({ roles: ["admin", "user"] }), async (req, res) => {
    const tenantId = req.auth.tenantId;
    const taskId = req.params.taskId;

    try {
      const task = await getTaskById({ tenantId, taskId });
      if (!task) return res.status(404).json({ error: "Task not found" });
      const report = exportTaskReport(task);
      res.setHeader("Content-Type", "text/markdown");
      return res.send(report);
    } catch (err) {
      return res.status(500).json({ error: String(err && err.message ? err.message : err) });
    }
  });
  app.get("/healthz", (_req, res) => {
    res.json({ ok: true, service: "agentic-ai-api", version: "1.0.0" });
  });
  return app;
}

module.exports = { createApiApp };

