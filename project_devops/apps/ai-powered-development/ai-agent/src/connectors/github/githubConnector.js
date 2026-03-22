const axios = require("axios");

function githubAuthHeaders(token) {
  return {
    Authorization: `token ${token}`,
    Accept: "application/vnd.github+json",
  };
}

function createGithubConnector({ githubToken }) {
  const api = axios.create({
    baseURL: "https://api.github.com",
    headers: githubAuthHeaders(githubToken),
    timeout: Number(process.env.GITHUB_API_TIMEOUT_MS || 30000),
  });

  async function getPullRequest({ owner, repo, pullNumber }) {
    const { data } = await api.get(`/repos/${owner}/${repo}/pulls/${pullNumber}`);
    return data;
  }

  async function listPullRequestFiles({ owner, repo, pullNumber, limitFiles }) {
    const perPage = 50;
    const { data } = await api.get(`/repos/${owner}/${repo}/pulls/${pullNumber}/files`, {
      params: { per_page: perPage },
    });
    if (!Array.isArray(data)) return [];
    const limit = limitFiles ? Number(limitFiles) : 10;
    return data.slice(0, limit).map((f) => ({
      filename: f.filename,
      status: f.status,
      additions: f.additions,
      deletions: f.deletions,
      changes: f.changes,
      patch: f.patch,
    }));
  }

  async function getFileContent({ owner, repo, path, ref }) {
    const { data } = await api.get(`/repos/${owner}/${repo}/contents/${encodeURIComponent(path)}`, {
      params: { ref },
    });
    if (!data || !data.content) return null;
    return Buffer.from(String(data.content), "base64").toString("utf8");
  }

  async function commentOnPullRequest({ owner, repo, pullNumber, body }) {
    const { data } = await api.post(`/repos/${owner}/${repo}/issues/${pullNumber}/comments`, {
      body,
    });
    return data;
  }

  return {
    getPullRequest,
    listPullRequestFiles,
    getFileContent,
    commentOnPullRequest,
  };
}

module.exports = { createGithubConnector };

