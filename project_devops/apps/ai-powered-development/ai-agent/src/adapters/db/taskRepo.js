const { getPool } = require("./pg");

async function createQueuedTask({ tenantId, taskType, repoOwner, repoName, prNumber, prHeadSha, maxAttempts }) {
  const pool = getPool();

  // Dedup: if there's already a queued/running task for same PR head, reuse it.
  const { rows: existing } = await pool.query(
    `SELECT * FROM agent_tasks
     WHERE tenant_id = $1
       AND task_type = $2
       AND repo_owner = $3
       AND repo_name = $4
       AND pr_number = $5
       AND pr_head_sha = $6
       AND status IN ('queued','running')
     ORDER BY created_at ASC
     LIMIT 1`,
    [tenantId, taskType, repoOwner, repoName, prNumber, prHeadSha]
  );
  if (existing[0]) return existing[0];

  const { rows } = await pool.query(
    `INSERT INTO agent_tasks (
       tenant_id, task_type, repo_owner, repo_name, pr_number, pr_head_sha,
       status, attempt_count, max_attempts
     )
     VALUES ($1,$2,$3,$4,$5,$6,'queued',0,$7)
     RETURNING *`,
    [tenantId, taskType, repoOwner, repoName, prNumber, prHeadSha, maxAttempts || 3]
  );
  return rows[0];
}

async function getTaskById({ tenantId, taskId }) {
  const pool = getPool();
  const { rows } = await pool.query(
    `SELECT * FROM agent_tasks WHERE id = $1 AND tenant_id = $2`,
    [taskId, tenantId]
  );
  return rows[0] || null;
}

async function claimNextQueuedTask({ tenantId }) {
  const pool = getPool();
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const { rows } = await client.query(
      `SELECT * FROM agent_tasks
       WHERE tenant_id = $1 AND status = 'queued'
       ORDER BY created_at ASC
       FOR UPDATE SKIP LOCKED
       LIMIT 1`,
      [tenantId]
    );
    if (!rows[0]) {
      await client.query("COMMIT");
      return null;
    }

    const task = rows[0];
    await client.query(
      `UPDATE agent_tasks
       SET status = 'running', updated_at = now()
       WHERE id = $1`,
      [task.id]
    );
    await client.query("COMMIT");
    return { ...task, status: "running" };
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }
}

function sanitizeString(str) {
  if (typeof str !== "string") return str;
  // eslint-disable-next-line no-control-regex
  return str.replace(/\u0000/g, "");
}

function sanitizeObject(obj) {
  if (!obj || typeof obj !== "object") return obj;
  if (Array.isArray(obj)) return obj.map(sanitizeObject);
  const newObj = {};
  for (const [k, v] of Object.entries(obj)) {
    newObj[k] = typeof v === "string" ? sanitizeString(v) : sanitizeObject(v);
  }
  return newObj;
}

async function updateTaskProgress({ tenantId, taskId, patch }) {
  const pool = getPool();
  // patch is a plain object with known keys
  const fields = [];
  const values = [];
  let i = 1;

  for (let [k, v] of Object.entries(patch)) {
    // Sanitize values to prevent Postgres UTF-8 0x00 errors
    v = typeof v === "string" ? sanitizeString(v) : sanitizeObject(v);

    fields.push(`${k} = $${i}`);
    if (v && typeof v === "object") {
      values.push(JSON.stringify(v));
    } else {
      values.push(v);
    }
    i += 1;
  }

  if (fields.length === 0) return;

  const tenantIdx = i;
  const taskIdx = i + 1;
  values.push(tenantId);
  values.push(taskId);

  const setSql = fields.join(", ");
  const sql = `UPDATE agent_tasks SET ${setSql}, updated_at = now()
               WHERE tenant_id = $${tenantIdx} AND id = $${taskIdx}`;

  try {
    await pool.query(sql, values);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error(`[dfte] updateTaskProgress failed for task ${taskId}:`, err.message);
    throw err;
  }
}

async function getTenantsWithQueuedTasks() {
  const pool = getPool();
  const { rows } = await pool.query(
    `SELECT tenant_id, MIN(created_at) as oldest_task 
     FROM agent_tasks 
     WHERE status = 'queued' 
     GROUP BY tenant_id 
     ORDER BY oldest_task ASC 
     LIMIT 50`
  );
  return rows.map((r) => r.tenant_id);
}

module.exports = {
  createQueuedTask,
  getTaskById,
  claimNextQueuedTask,
  updateTaskProgress,
  getTenantsWithQueuedTasks,
};

