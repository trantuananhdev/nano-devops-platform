const axios = require("axios");

function githubAuthHeaders(token) {
  return {
    Authorization: `token ${token}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

function createGithubConnector({ githubToken }) {
  const api = axios.create({
    baseURL: "https://api.github.com",
    headers: githubAuthHeaders(githubToken),
    timeout: Number(process.env.GITHUB_API_TIMEOUT_MS || 30000),
  });

  // ─── Existing ────────────────────────────────────────────────────────────

  async function getPullRequest({ owner, repo, pullNumber }) {
    const { data } = await api.get(`/repos/${owner}/${repo}/pulls/${pullNumber}`);
    return data;
  }

  async function listPullRequestFiles({ owner, repo, pullNumber, limitFiles }) {
    const { data } = await api.get(`/repos/${owner}/${repo}/pulls/${pullNumber}/files`, {
      params: { per_page: 50 },
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
    const { data } = await api.get(
      `/repos/${owner}/${repo}/contents/${encodeURIComponent(path)}`,
      { params: { ref } }
    );
    if (!data || !data.content) return null;
    return Buffer.from(String(data.content), "base64").toString("utf8");
  }

  async function commentOnPullRequest({ owner, repo, pullNumber, body }) {
    const { data } = await api.post(
      `/repos/${owner}/${repo}/issues/${pullNumber}/comments`,
      { body }
    );
    return data;
  }

  // ─── New: repo info ───────────────────────────────────────────────────────

  async function getDefaultBranch({ owner, repo }) {
    const { data } = await api.get(`/repos/${owner}/${repo}`);
    return data.default_branch || "main";
  }

  async function getBranchSha({ owner, repo, branch }) {
    const { data } = await api.get(`/repos/${owner}/${repo}/git/ref/heads/${encodeURIComponent(branch)}`);
    return data.object.sha;
  }

  // ─── New: create branch ───────────────────────────────────────────────────

  async function createBranch({ owner, repo, branchName, fromSha }) {
    const { data } = await api.post(`/repos/${owner}/${repo}/git/refs`, {
      ref: `refs/heads/${branchName}`,
      sha: fromSha,
    });
    return data;
  }

  // ─── New: push changed files as a single commit via Git Data API ──────────
  // changedFiles: array of { path: string, content: string }
  // Dùng Git Trees API để commit toàn bộ trong 1 request, không cần file-by-file.

  async function pushDiffCommit({ owner, repo, branchName, baseSha, changedFiles, commitMessage }) {
    if (!changedFiles || changedFiles.length === 0) {
      throw new Error("pushDiffCommit: changedFiles is empty");
    }

    // 1. Tạo blob cho từng file
    const blobs = await Promise.all(
      changedFiles.map(async (f) => {
        const { data } = await api.post(`/repos/${owner}/${repo}/git/blobs`, {
          content: Buffer.from(f.content, "utf8").toString("base64"),
          encoding: "base64",
        });
        return { path: f.path, sha: data.sha, mode: "100644", type: "blob" };
      })
    );

    // 2. Tạo tree mới dựa trên base tree
    const { data: treeData } = await api.post(`/repos/${owner}/${repo}/git/trees`, {
      base_tree: baseSha,
      tree: blobs,
    });

    // 3. Tạo commit
    const { data: commitData } = await api.post(`/repos/${owner}/${repo}/git/commits`, {
      message: commitMessage,
      tree: treeData.sha,
      parents: [baseSha],
      author: {
        name: process.env.GIT_USER_NAME || "Ghost Engineer",
        email: process.env.GIT_USER_EMAIL || "ghost@nano.platform",
        date: new Date().toISOString(),
      },
    });

    // 4. Update branch ref
    await api.patch(`/repos/${owner}/${repo}/git/refs/heads/${encodeURIComponent(branchName)}`, {
      sha: commitData.sha,
      force: false,
    });

    return commitData;
  }

  // ─── New: create pull request ─────────────────────────────────────────────

  async function createPullRequest({ owner, repo, title, body, head, base }) {
    const { data } = await api.post(`/repos/${owner}/${repo}/pulls`, {
      title,
      body,
      head,
      base: base || "main",
      draft: false,
    });
    return data;
  }

  return {
    // existing
    getPullRequest,
    listPullRequestFiles,
    getFileContent,
    commentOnPullRequest,
    // new
    getDefaultBranch,
    getBranchSha,
    createBranch,
    pushDiffCommit,
    createPullRequest,
  };
}

module.exports = { createGithubConnector };