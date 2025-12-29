const path = require("path");
const fs = require("fs");
const { updateTaskProgress } = require("../adapters/db/taskRepo");
const { createLlmProvider } = require("../llm/providerFactory");
const { findTenantByRepoFullName } = require("../adapters/db/githubRepoMappingRepo");
const { createGithubConnector } = require("../connectors/github/githubConnector");
const { cloneRepo, applyDiffFromFile, getWorkingDiff, cleanupSandbox } = require("../sandbox/repoSandbox");
const { runTestsVerified } = require("../verification/runTests");
const { extractUnifiedDiff } = require("./extractUnifiedDiff");

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function truncate(str, max) {
  if (!str) return "";
  if (str.length <= max) return str;
  return str.slice(0, max) + `\n...<truncated ${str.length - max} chars>`;
}

function slugify(str) {
  return String(str || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
}

/**
 * Đọc toàn bộ source files trong repo, ưu tiên file quan trọng.
 * Trả về string context để đưa vào LLM prompt.
 */
function readRepoContext(repoDir, maxTotalChars = 8000) {
  const IGNORE = new Set(["node_modules", ".git", "dist", "build", "__pycache__", ".venv", "vendor", "target"]);
  const EXTS   = new Set([".js", ".ts", ".py", ".go", ".java", ".php", ".rb", ".rs"]);

  const files = [];
  function walk(dir) {
    let entries;
    try { entries = fs.readdirSync(dir); } catch { return; }
    for (const name of entries) {
      if (IGNORE.has(name)) continue;
      const full = path.join(dir, name);
      let stat;
      try { stat = fs.statSync(full); } catch { continue; }
      if (stat.isDirectory()) walk(full);
      else if (EXTS.has(path.extname(name).toLowerCase())) files.push(full);
    }
  }
  walk(repoDir);

  const priority = ["server.js", "app.py", "main.go", "index.js", "index.ts", "main.py", "index.php", "App.java"];
  files.sort((a, b) => {
    const ai = priority.indexOf(path.basename(a));
    const bi = priority.indexOf(path.basename(b));
    if (ai !== -1 && bi === -1) return -1;
    if (bi !== -1 && ai === -1) return 1;
    return a.length - b.length; // file gần root lên trước
  });

  let total = 0;
  const parts = [];
  for (const f of files) {
    if (total >= maxTotalChars) break;
    let content;
    try { content = fs.readFileSync(f, "utf8"); } catch { continue; }
    const rel     = path.relative(repoDir, f);
    const snippet = truncate(content, Math.min(2000, maxTotalChars - total));
    parts.push(`### File: ${rel}\n\`\`\`\n${snippet}\n\`\`\``);
    total += snippet.length;
  }

  return parts.length > 0
    ? `\n\n## Source Code Context (${files.length} files found)\n${parts.join("\n\n")}`
    : "";
}

/**
 * Lấy danh sách files đã thay đổi trong sandbox sau khi apply patch.
 * Trả về array { path, content } để push lên GitHub.
 */
function getChangedFilesFromSandbox(repoDir) {
  const { execSync } = require("child_process");
  let output = "";
  try {
    output = execSync("git diff HEAD --name-only", { cwd: repoDir, encoding: "utf8" });
  } catch {
    return [];
  }
  const result = [];
  for (const relPath of output.trim().split("\n").filter(Boolean)) {
    try {
      const content = fs.readFileSync(path.join(repoDir, relPath), "utf8");
      result.push({ path: relPath, content });
    } catch {
      // file deleted — skip
    }
  }
  return result;
}

// ─────────────────────────────────────────────
// LLM Prompts
// ─────────────────────────────────────────────

function buildAnalysisPrompt({ metadata, logs, codeContext }) {
  return `You are "The Ghost Engineer", an autonomous SRE and Developer.

## Incident
- **Container**: ${metadata.containerName} (Image: ${metadata.image})
- **Action**: ${metadata.action}
- **Exit Code**: ${metadata.exitCode}
- **Node**: ${metadata.nodeName}

## Last 100 Log Lines
\`\`\`
${logs}
\`\`\`
${codeContext}

## Your Task
1. Identify the **root cause** (Memory Leak, Race Condition, crash, etc.)
2. Explain clearly what went wrong (max 150 words).
3. Output a **unified diff patch** inside a \`\`\`diff block.
4. If you cannot produce a patch, output an empty diff block.

Rules:
- Output ONE unified diff inside a single \`\`\`diff code block after your explanation.
- Format response in Markdown.`;
}

function buildRetryPrompt({ metadata, previousDiff, testOutput, attemptNo, maxAttempts }) {
  return `You are "The Ghost Engineer". Your previous patch failed verification.

## Attempt ${attemptNo} / ${maxAttempts}
- **Container**: ${metadata.containerName}

## Verification Failure
\`\`\`
${truncate(testOutput, 2000)}
\`\`\`

## Your Previous Patch
\`\`\`diff
${truncate(previousDiff, 2000)}
\`\`\`

Fix the patch so verification passes. Output ONLY a corrected unified diff inside a \`\`\`diff block. No explanation.`;
}

// ─────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────

async function runIncidentFixTask(task) {
  const { id, tenant_id, logs, repo_owner, repo_name } = task;

  // metadata từ DB có thể là string JSON hoặc object
  let metadata = task.metadata;
  if (typeof metadata === "string") {
    try { metadata = JSON.parse(metadata); } catch { metadata = {}; }
  }
  metadata = metadata || {};

  console.log(`[ghost-engineer] 👻 Task ${id} | container=${metadata.containerName}`);

  let sandbox = null;
  const maxAttempts = Number(process.env.INCIDENT_MAX_ATTEMPTS || 3);

  try {
    await updateTaskProgress({
      tenantId: tenant_id,
      taskId: id,
      patch: { status: "running", progress_report: "Ghost Engineer is reading the incident..." },
    });

    if (!metadata.containerName || !logs) {
      throw new Error("Missing metadata or logs in task payload");
    }

    // ── Step 1: Clone repo ───────────────────────────────────────────────
    let codeContext = "";
    let hasSandbox  = false;
    let tenantRow   = null;
    let github      = null;

    if (repo_owner && repo_owner !== "unknown") {
      const repoFullName = `${repo_owner}/${repo_name}`;
      try {
        tenantRow = await findTenantByRepoFullName({ repoFullName });
        const githubToken = (tenantRow && tenantRow.github_token) || process.env.GITHUB_TOKEN;

        if (githubToken) {
          github = createGithubConnector({ githubToken });

          console.log(`[ghost-engineer] Cloning ${repoFullName}...`);
          await updateTaskProgress({
            tenantId: tenant_id, taskId: id,
            patch: { progress_report: `Cloning ${repoFullName}...` },
          });

          sandbox = await cloneRepo({
            repoOwner:     repo_owner,
            repoName:      repo_name,
            githubToken:   githubToken,
            // Senior Fix: Ưu tiên HTTPS qua Token nếu có, tránh lỗi SSH key libcrypto
            useSsh:        !githubToken && !!(tenantRow && tenantRow.ssh_key || process.env.GITHUB_SSH_KEY_FILE),
            sshKeyContent: tenantRow ? tenantRow.ssh_key : null,
            sshKeyPath:    process.env.GITHUB_SSH_KEY_FILE,
          });

          codeContext = readRepoContext(sandbox.dir);
          hasSandbox  = true;
          console.log(`[ghost-engineer] Cloned. Context: ${codeContext.length} chars`);
        } else {
          console.warn(`[ghost-engineer] No GitHub token found for ${repoFullName}. Analysis only.`);
        }
      } catch (cloneErr) {
        console.warn(`[ghost-engineer] Clone failed (analysis only): ${cloneErr.message}`);
      }
    }

    const llm = createLlmProvider();

    // ── Step 2: LLM phân tích + sinh patch lần đầu ──────────────────────
    await updateTaskProgress({
      tenantId: tenant_id, taskId: id,
      patch: { progress_report: "Analyzing logs and generating patch..." },
    });

    const analysisText = await llm.chatText({
      messages: [
        { role: "system", content: "You are The Ghost Engineer, a senior SRE/DevOps expert. Always produce a unified diff patch when source code is available." },
        { role: "user",   content: buildAnalysisPrompt({ metadata, logs, codeContext }) },
      ],
    });

    let currentDiff  = extractUnifiedDiff(analysisText);
    let lastTestResult = null;
    let attemptsUsed = 1;
    let testPassed   = false;

    // ── Step 3: Self-Correction Loop ─────────────────────────────────────
    if (hasSandbox && currentDiff) {
      console.log(`[ghost-engineer] Self-Correction Loop — max ${maxAttempts} attempts`);

      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        attemptsUsed = attempt;
        await updateTaskProgress({
          tenantId: tenant_id, taskId: id,
          patch: { progress_report: `Attempt ${attempt}/${maxAttempts}: applying patch + verifying...` },
        });

        // Apply patch
        console.log(`[ghost-engineer] Applying patch (length: ${currentDiff.length} chars). First 10 lines:\n${currentDiff.split("\n").slice(0, 10).join("\n")}`);
        const applyRes = await applyDiffFromFile({ repoDir: sandbox.dir, diffText: currentDiff });
        if (applyRes.exitCode !== 0) {
          console.warn(`[ghost-engineer] git apply failed (attempt ${attempt}): ${applyRes.stderr}`);
          if (attempt < maxAttempts) {
            const retryText = await llm.chatText({
              messages: [
                { role: "system", content: "You are The Ghost Engineer. Fix the patch." },
                { role: "user",   content: buildRetryPrompt({
                    metadata, previousDiff: currentDiff,
                    testOutput: `git apply failed:\n${applyRes.stderr}`,
                    attemptNo: attempt + 1, maxAttempts,
                  })},
              ],
            });
            currentDiff = extractUnifiedDiff(retryText) || currentDiff;
          }
          continue;
        }

        // Verify (test / build / syntax check tùy stack)
        lastTestResult = await runTestsVerified({ repoDir: sandbox.dir, skipInstall: attempt > 1 });

        if (lastTestResult.passed) {
          testPassed = true;
          console.log(`[ghost-engineer] ✅ Verification PASSED on attempt ${attempt} (stage: ${lastTestResult.stage})`);
          break;
        }

        console.log(`[ghost-engineer] ❌ Verification failed (attempt ${attempt}) stage=${lastTestResult.stage}`);

        if (attempt < maxAttempts) {
          await updateTaskProgress({
            tenantId: tenant_id, taskId: id,
            patch: { progress_report: `Verification failed (attempt ${attempt}). Self-correcting patch...` },
          });
          const testOutput = `${lastTestResult.stderr || ""}\n${lastTestResult.stdout || ""}`.trim();
          const retryText  = await llm.chatText({
            messages: [
              { role: "system", content: "You are The Ghost Engineer. Fix the patch so verification passes." },
              { role: "user",   content: buildRetryPrompt({
                  metadata, previousDiff: currentDiff,
                  testOutput, attemptNo: attempt + 1, maxAttempts,
                })},
            ],
          });
          const newDiff = extractUnifiedDiff(retryText);
          if (newDiff) currentDiff = newDiff;
        }
      }
    } else if (hasSandbox && !currentDiff) {
      console.log("[ghost-engineer] LLM produced no patch — analysis only.");
    } else {
      console.log("[ghost-engineer] No sandbox — analysis only.");
    }

    // Lấy diff thực tế từ sandbox
    let finalDiff = currentDiff || "";
    if (hasSandbox) {
      const diffRes = await getWorkingDiff({ repoDir: sandbox.dir });
      if (diffRes.exitCode === 0 && diffRes.diff) finalDiff = diffRes.diff;
    }

    // ── Step 4: Tạo GitHub PR nếu verification pass ──────────────────────
    let prUrl     = null;
    let prNumber  = null;
    let branchName = null;

    if (testPassed && hasSandbox && github && finalDiff) {
      try {
        await updateTaskProgress({
          tenantId: tenant_id, taskId: id,
          patch: { progress_report: "Verification passed! Creating GitHub Pull Request..." },
        });

        const timestamp = Date.now();
        branchName = `ghost/fix-${slugify(metadata.containerName)}-${timestamp}`;

        const defaultBranch = await github.getDefaultBranch({ owner: repo_owner, repo: repo_name });
        const baseSha       = await github.getBranchSha({ owner: repo_owner, repo: repo_name, branch: defaultBranch });

        await github.createBranch({ owner: repo_owner, repo: repo_name, branchName, fromSha: baseSha });
        console.log(`[ghost-engineer] Branch created: ${branchName}`);

        const changedFiles = getChangedFilesFromSandbox(sandbox.dir);

        if (changedFiles.length > 0) {
          const firstLine  = analysisText.split("\n").find((l) => l.trim()) || "fix incident";
          const commitMsg  = `fix(ghost-engineer): ${truncate(firstLine, 72)}\n\nAutomated fix by Ghost Engineer\nTask: ${id}\nContainer: ${metadata.containerName}\nAttempts: ${attemptsUsed}`;

          await github.pushDiffCommit({
            owner: repo_owner, repo: repo_name,
            branchName, baseSha, changedFiles,
            commitMessage: commitMsg,
          });
          console.log(`[ghost-engineer] Pushed ${changedFiles.length} file(s) to ${branchName}`);

          const verifyLine = lastTestResult
            ? `${lastTestResult.passed ? "✅" : "❌"} ${lastTestResult.stage} — Stack: ${lastTestResult.stack} — Attempts: ${attemptsUsed}`
            : "⏭️ Verification skipped";

          const prBody = `## 👻 Ghost Engineer: Automated Incident Fix

**Container**: \`${metadata.containerName}\`
**Image**: \`${metadata.image}\`
**Trigger**: ${metadata.action} (exit code: \`${metadata.exitCode}\`)
**Node**: ${metadata.nodeName}
**Task ID**: \`${id}\`

---

### Root Cause Analysis

${truncate(analysisText, 2000)}

---

### Verification

${verifyLine}

### Patch Applied

\`\`\`diff
${truncate(finalDiff, 3000)}
\`\`\`

---
*This PR was created automatically by Ghost Engineer. Please review before merging.*`;

          const pr = await github.createPullRequest({
            owner: repo_owner, repo: repo_name,
            title: `[Ghost Engineer] fix(${metadata.containerName}): ${truncate(firstLine, 60)}`,
            body:  prBody,
            head:  branchName,
            base:  defaultBranch,
          });

          prUrl    = pr.html_url;
          prNumber = pr.number;
          console.log(`[ghost-engineer] ✅ PR created: ${prUrl}`);
        } else {
          console.warn("[ghost-engineer] No changed files in sandbox — skipping PR");
        }
      } catch (prErr) {
        // Không fail task vì PR lỗi
        console.error(`[ghost-engineer] PR creation failed: ${prErr.message}`);
      }
    }

    // ── Step 5: Save final result ─────────────────────────────────────────
    const testSection = lastTestResult
      ? `\n\n## Verification\n- **Status**: ${lastTestResult.passed ? "✅ PASSED" : "❌ FAILED"}\n- **Stage**: ${lastTestResult.stage}\n- **Stack**: ${lastTestResult.stack}\n- **Attempts**: ${attemptsUsed}/${maxAttempts}`
      : "\n\n## Verification\n- **Status**: ⏭️ Skipped";

    const prSection = prUrl
      ? `\n\n## Pull Request\n[${branchName}](${prUrl}) — PR #${prNumber} opened, ready for review.`
      : testPassed
        ? "\n\n## Pull Request\n⚠️ PR creation failed — patch verified but not pushed. Check GitHub token permissions (`repo` scope required)."
        : "\n\n## Pull Request\n⏳ Not created — verification did not pass.";

    const firstLine = analysisText.split("\n").find((l) => l.trim()) || "See analysis";

    const proposal = `### 👻 Ghost Engineer: Incident Fix Report

**Container**: \`${metadata.containerName}\`
**Image**: \`${metadata.image}\`
**Trigger**: ${metadata.action} (exit code: ${metadata.exitCode})
${testSection}
${prSection}

---

${truncate(analysisText, 3000)}

${finalDiff ? `\n## Final Patch\n\`\`\`diff\n${truncate(finalDiff, 4000)}\n\`\`\`` : ""}`;

    const progressMsg = prUrl
      ? `✅ Verification passed + PR #${prNumber} created: ${prUrl}`
      : testPassed
        ? `✅ Verification passed after ${attemptsUsed} attempt(s). PR creation failed — check GitHub token.`
        : `Analysis complete. Verification ${lastTestResult ? "failed" : "skipped"}. Human review required.`;

    await updateTaskProgress({
      tenantId: tenant_id,
      taskId:   id,
      patch: {
        status:          "completed",
        attempt_count:   attemptsUsed,
        analysis_result: analysisText,
        result: {
          proposal,
          rootCause:    firstLine,
          testPassed,
          attemptsUsed,
          hasPatch:     !!finalDiff,
          prUrl,
          prNumber,
          branchName,
        },
        progress_report: progressMsg,
      },
    });

    console.log(`[ghost-engineer] ✅ Task ${id} done. testPassed=${testPassed} prUrl=${prUrl || "none"}`);

  } catch (err) {
    console.error(`[ghost-engineer] ❌ Task ${id} failed:`, err);
    await updateTaskProgress({
      tenantId: tenant_id,
      taskId:   id,
      patch: {
        status:          "failed",
        progress_report: String(err && err.message ? err.message : err),
      },
    });
  } finally {
    if (sandbox) cleanupSandbox(sandbox);
  }
}

module.exports = { runIncidentFixTask };