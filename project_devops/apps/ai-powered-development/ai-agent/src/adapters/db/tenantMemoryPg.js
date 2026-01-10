const { getPool } = require("./pg");

async function getTenantMemory(tenantId) {
  const pool = getPool();
  const { rows } = await pool.query(
    `SELECT tenant_id, today, projects, patterns, active_tasks, updated_at
     FROM tenant_memory WHERE tenant_id = $1`,
    [tenantId]
  );
  return rows[0] || null;
}

async function upsertTenantMemory(tenantId, patch) {
  const pool = getPool();
  const existing = await getTenantMemory(tenantId);
  const base = existing || { today: {}, projects: {}, patterns: {}, active_tasks: {} };

  const next = {
    today: patch.today !== undefined ? patch.today : base.today,
    projects: patch.projects !== undefined ? patch.projects : base.projects,
    patterns: patch.patterns !== undefined ? patch.patterns : base.patterns,
    active_tasks: patch.active_tasks !== undefined ? patch.active_tasks : base.active_tasks,
  };

  await pool.query(
    `INSERT INTO tenant_memory (tenant_id, today, projects, patterns, active_tasks)
     VALUES ($1, $2, $3, $4, $5)
     ON CONFLICT (tenant_id) DO UPDATE SET
       today = EXCLUDED.today,
       projects = EXCLUDED.projects,
       patterns = EXCLUDED.patterns,
       active_tasks = EXCLUDED.active_tasks,
       updated_at = now()`,
    [tenantId, next.today, next.projects, next.patterns, next.active_tasks]
  );
}

async function addLessonIfPass({ tenantId, lesson }) {
  const pool = getPool();
  const existing = await getTenantMemory(tenantId);
  const today = existing ? existing.today : {};
  const lessons = Array.isArray(today.lessons) ? today.lessons : [];
  const nextLessons = [lesson, ...lessons].slice(0, 50);
  const nextToday = { ...today, lessons: nextLessons };
  await upsertTenantMemory(tenantId, { today: nextToday });
}

async function addPattern({ tenantId, pattern }) {
  const existing = await getTenantMemory(tenantId);
  const patterns = Array.isArray(existing?.patterns) ? existing.patterns : [];
  // Basic deduplication by title
  const nextPatterns = [pattern, ...patterns.filter((p) => p.title !== pattern.title)].slice(0, 20);
  await upsertTenantMemory(tenantId, { patterns: nextPatterns });
}

module.exports = { getTenantMemory, upsertTenantMemory, addLessonIfPass, addPattern };

