const { getPool } = require("./pg");

async function initDb() {
  const pool = getPool();
  // eslint-disable-next-line no-console
  console.log("[dfte] Initializing Agentic-AI Database schema...");
  const client = await pool.connect();
  try {
    try {
      await client.query(`CREATE EXTENSION IF NOT EXISTS "pgcrypto";`);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("[dfte] Warning: Failed to create pgcrypto extension. This might be fine if it's already installed or not required by current schema.", err.message);
    }

    await client.query(`
      CREATE TABLE IF NOT EXISTS tenant_github_repos (
        tenant_id TEXT NOT NULL,
        repo_full_name TEXT NOT NULL,
        github_token TEXT,
        ssh_key TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, repo_full_name)
      );
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS tenant_memory (
        tenant_id TEXT PRIMARY KEY,
        today JSONB NOT NULL DEFAULT '{}'::jsonb,
        projects JSONB NOT NULL DEFAULT '{}'::jsonb,
        patterns JSONB NOT NULL DEFAULT '{}'::jsonb,
        active_tasks JSONB NOT NULL DEFAULT '{}'::jsonb,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );
    `);

    await client.query(`
      CREATE TABLE IF NOT EXISTS agent_tasks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL,
        task_type TEXT NOT NULL,
        repo_owner TEXT NOT NULL,
        repo_name TEXT NOT NULL,
        pr_number INTEGER NOT NULL,
        pr_head_sha TEXT NOT NULL,
        status TEXT NOT NULL,
        attempt_count INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL DEFAULT 3,
        last_error TEXT,
        progress_report TEXT,
        logs TEXT,
        metadata JSONB,
        analysis_result TEXT,
        result JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );
    `);

    // Migration for existing DB
    await client.query(`ALTER TABLE agent_tasks ADD COLUMN IF NOT EXISTS logs TEXT;`);
    await client.query(`ALTER TABLE agent_tasks ADD COLUMN IF NOT EXISTS metadata JSONB;`);
    await client.query(`ALTER TABLE agent_tasks ADD COLUMN IF NOT EXISTS analysis_result TEXT;`);
    await client.query(`ALTER TABLE agent_tasks ADD COLUMN IF NOT EXISTS progress_report TEXT;`);
    await client.query(`ALTER TABLE tenant_github_repos ADD COLUMN IF NOT EXISTS github_token TEXT;`);
    await client.query(`ALTER TABLE tenant_github_repos ADD COLUMN IF NOT EXISTS ssh_key TEXT;`);

    // Basic indexes for worker queues.
    await client.query(`CREATE INDEX IF NOT EXISTS agent_tasks_status_idx ON agent_tasks(status);`);
    await client.query(`CREATE INDEX IF NOT EXISTS agent_tasks_tenant_status_idx ON agent_tasks(tenant_id, status);`);

    // Senior DevOps: Auto-provision demo tenant if Repo Name is provided
    const repoName = process.env.BOOTSTRAP_REPO_FULL_NAME;
    const token = process.env.BOOTSTRAP_GITHUB_TOKEN;
    const sshKey = process.env.BOOTSTRAP_SSH_KEY;

    if (repoName && (token || sshKey)) {
      await client.query(`
        INSERT INTO tenant_github_repos (tenant_id, repo_full_name, github_token, ssh_key)
        VALUES ('tenant-1', $1, $2, $3)
        ON CONFLICT (tenant_id, repo_full_name) 
        DO UPDATE SET github_token = EXCLUDED.github_token, ssh_key = EXCLUDED.ssh_key;
      `, [repoName, token || null, sshKey || null]);
    }
  } finally {
    client.release();
  }
}

module.exports = { initDb };

