const { getPool } = require("./pg");

async function upsertTenantRepoCredential({ tenantId, repoFullName, githubToken }) {
  const pool = getPool();
  const { rows } = await pool.query(
    `INSERT INTO tenant_github_repos (tenant_id, repo_full_name, github_token)
     VALUES ($1,$2,$3)
     ON CONFLICT (tenant_id, repo_full_name)
     DO UPDATE SET github_token = EXCLUDED.github_token, updated_at = now()
     RETURNING *`,
    [tenantId, repoFullName, githubToken]
  );
  return rows[0];
}

async function findTenantByRepoFullName({ repoFullName }) {
  const pool = getPool();
  const { rows } = await pool.query(
    `SELECT tenant_id, github_token, ssh_key, repo_full_name
     FROM tenant_github_repos
     WHERE repo_full_name = $1
     LIMIT 1`,
    [repoFullName]
  );
  return rows[0] || null;
}

module.exports = { upsertTenantRepoCredential, findTenantByRepoFullName };

