const path = require("path");
const fs = require("fs");
const { updateTaskProgress } = require("../adapters/db/taskRepo");
const { createLlmProvider } = require("../llm/providerFactory");
const { findTenantByRepoFullName } = require("../adapters/db/githubRepoMappingRepo");
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

/**
 * Đọc tất cả source files trong repo (loại bỏ node_modules, .git, build artifacts).
 * Trả về string tổng hợp để đưa vào context LLM.
 */
function readRepoContext(repoDir, maxTotalChars = 8000) {
  const IGNORE = new Set(["node_modules", ".git", "dist", "build", "__pycache__", ".venv", "vendor"]);
  const EXTS = new Set([".js", ".ts", ".py", ".go", ".java", ".rb", ".rs"]);

  const files = [];
  function walk(dir) {
    let entries;
    try { entries = fs.readdirSync(dir); } catch { return; }
    for (const name of entries) {
      if (IGNORE.has(name)) continue;
      const full = path.join(dir, name);
      let stat;
      try { stat = fs.statSync(full); } catch { continue; }
      if (stat.isDirectory()) {
        walk(full);
      } else if (EXTS.has(path.extname(name).toLowerCase())) {
        files.push(full);
      }
    }
  }
  walk(repoDir);

  // Prioritize: server.js / app.py / main.go / index.js first
  const priority = ["server.js", "app.py", "main.go", "index.js", "index.ts", "main.py"];
  files.sort((a, b) => {
    const ai = priority.indexOf(path.basename(a));
    const bi = priority.indexOf(path.basename(b));
    if (ai !== -1 && bi === -1) return -1;
    if (bi !== -1 && ai === -1) return 1;
    return a.length - b.length; // shorter path = closer to root = more important
  });

  let total = 0;
  const parts = [];
  for (const f of files) {
    if (total >= maxTotalChars) break;
    let content;
    try { content = fs.readFileSync(f, "utf8"); } catch { continue; }
    const rel = path.relative(repoDir, f);
    const snippet = truncate(content, Math.min(2000, maxTotalChars - total));
    parts.push(`### File: ${rel}\n\`\`\`\n${snippet}\n\`\`\``);
    total += snippet.length;
  }

  return parts.length > 0
    ? `\n\n## Source Code Context (${files.length} files found)\n${parts.join("\n\n")}`
    : "";
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
1. Identify the **root cause** (Memory Leak, Race Condition, unhandled exception, etc.)
2. Explain clearly what went wrong.
3. Output a **unified diff patch** that fixes the issue inside a \`\`\`diff block.
4. If you cannot produce a patch (e.g. no source available), output an empty diff block.

Rules:
- Output ONLY a single unified diff inside a \`\`\`diff code block after your explanation.
- Keep the explanation concise (under 200 words).
- Format response in Markdown.`;
}

function buildRetryPrompt({ metadata, logs, previousDiff, testOutput, attemptNo, maxAttempts }) {
  return `You are "The Ghost Engineer". Your previous patch failed the test suite.

## Attempt ${attemptNo} / ${maxAttempts}

## Incident
- **Container**: ${metadata.containerName}
- **Exit Code**: ${metadata.exitCode}

## Test Failure Output
\`\`\`
${truncate(testOutput, 2000)}
\`\`\`

## Your Previous Patch
\`\`\`diff
${truncate(previousDiff, 2000)}
\`\`\`

## Your Task
Fix the patch so tests pass. Output ONLY a corrected unified diff inside a \`\`\`diff block.
Do not explain — just output the fixed diff.`;
}

// ─────────────────────────────────────────────
// Main task
// ─────────────────────────────────────────────

async function runIncidentFixTask(task) {
  const { id, tenant_id, logs, repo_owner, repo_name } = task;

  // Parse metadata — DB trả về JSONB có thể là string hoặc object
  let metadata = task.metadata;
  if (typeof metadata === "string") {
    try { metadata = JSON.parse(metadata); } catch { metadata = {}; }
  }
  metadata = metadata || {};

  console.log(`[ghost-engineer] 👻 Analyzing incident for task ${id} | container=${metadata.containerName}`);

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

    // ── Step 1: Clone repo để lấy code context ────────────────────────────
    let codeContext = "";
    let hasSandbox = false;

    if (repo_owner && repo_owner !== "unknown") {
      const repoFullName = `${repo_owner}/${repo_name}`;
      try {
        const tenantRow = await findTenantByRepoFullName({ repoFullName });
        if (tenantRow) {
          console.log(`[ghost-engineer] Cloning ${repoFullName}...`);
          await updateTaskProgress({
            tenantId: tenant_id,
            taskId: id,
            patch: { progress_report: `Cloning ${repoFullName} for code context...` },
          });

          sandbox = await cloneRepo({
            repoOwner: repo_owner,
            repoName: repo_name,
            githubToken: tenantRow.github_token,
            useSsh: !!(tenantRow.ssh_key || process.env.GITHUB_SSH_KEY_FILE),
            sshKeyContent: tenantRow.ssh_key,
            sshKeyPath: process.env.GITHUB_SSH_KEY_FILE,
          });

          codeContext = readRepoContext(sandbox.dir);
          hasSandbox = true;
          console.log(`[ghost-engineer] Code context: ${codeContext.length} chars from ${repo_name}`);
        }
      } catch (cloneErr) {
        console.warn(`[ghost-engineer] Clone failed (proceeding without code): ${cloneErr.message}`);
      }
    }

    const llm = createLlmProvider();

    // ── Step 2: LLM phân tích + tạo patch lần đầu ────────────────────────
    await updateTaskProgress({
      tenantId: tenant_id,
      taskId: id,
      patch: { progress_report: "Ghost Engineer is analyzing logs and generating patch..." },
    });

    const analysisText = await llm.chatText({
      messages: [
        { role: "system", content: "You are The Ghost Engineer, a senior SRE/DevOps expert. Always produce a unified diff patch." },
        { role: "user", content: buildAnalysisPrompt({ metadata, logs, codeContext }) },
      ],
    });

    let currentDiff = extractUnifiedDiff(analysisText);
    let lastTestResult = null;
    let attemptsUsed = 1;
    let finalStatus = "completed";

    // ── Step 3: Self-Correction Loop (chỉ chạy nếu có sandbox + có patch) ─
    if (hasSandbox && currentDiff) {
      console.log(`[ghost-engineer] Starting Self-Correction Loop (max ${maxAttempts} attempts)...`);

      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        attemptsUsed = attempt;

        await updateTaskProgress({
          tenantId: tenant_id,
          taskId: id,
          patch: { progress_report: `Attempt ${attempt}/${maxAttempts}: Applying patch and running tests...` },
        });

        // Apply patch
        const applyRes = await applyDiffFromFile({ repoDir: sandbox.dir, diffText: currentDiff });
        if (applyRes.exitCode !== 0) {
          console.warn(`[ghost-engineer] Patch apply failed (attempt ${attempt}): ${applyRes.stderr}`);
          // Patch không áp dụng được — nhờ LLM sửa ngay
          if (attempt < maxAttempts) {
            const retryText = await llm.chatText({
              messages: [
                { role: "system", content: "You are The Ghost Engineer. Fix the patch so it applies cleanly." },
                { role: "user", content: buildRetryPrompt({
                  metadata, logs,
                  previousDiff: currentDiff,
                  testOutput: `git apply failed:\n${applyRes.stderr}`,
                  attemptNo: attempt + 1,
                  maxAttempts,
                })},
              ],
            });
            currentDiff = extractUnifiedDiff(retryText) || currentDiff;
          }
          continue;
        }

        // Run tests
        console.log(`[ghost-engineer] Running tests (attempt ${attempt})...`);
        lastTestResult = await runTestsVerified({ repoDir: sandbox.dir, skipInstall: attempt > 1 });

        if (lastTestResult.passed) {
          console.log(`[ghost-engineer] ✅ Tests passed on attempt ${attempt}!`);
          finalStatus = "completed";
          break;
        }

        console.log(`[ghost-engineer] ❌ Tests failed (attempt ${attempt}). Exit: ${lastTestResult.exitCode}`);

        if (attempt < maxAttempts) {
          await updateTaskProgress({
            tenantId: tenant_id,
            taskId: id,
            patch: { progress_report: `Tests failed (attempt ${attempt}). Asking LLM to self-correct...` },
          });

          const testOutput = `${lastTestResult.stderr || ""}\n${lastTestResult.stdout || ""}`.trim();
          const retryText = await llm.chatText({
            messages: [
              { role: "system", content: "You are The Ghost Engineer. Fix the patch so tests pass." },
              { role: "user", content: buildRetryPrompt({
                metadata, logs,
                previousDiff: currentDiff,
                testOutput,
                attemptNo: attempt + 1,
                maxAttempts,
              })},
            ],
          });

          const newDiff = extractUnifiedDiff(retryText);
          if (newDiff) {
            currentDiff = newDiff;
          }
        } else {
          finalStatus = "completed"; // Vẫn complete — human review
        }
      }
    } else if (hasSandbox && !currentDiff) {
      console.log("[ghost-engineer] No patch generated — analysis only.");
    } else {
      console.log("[ghost-engineer] No sandbox — analysis only (no test loop).");
    }

    // ── Step 4: Lấy diff cuối cùng từ sandbox ────────────────────────────
    let finalDiff = currentDiff || "";
    if (hasSandbox) {
      const diffRes = await getWorkingDiff({ repoDir: sandbox.dir });
      if (diffRes.exitCode === 0 && diffRes.diff) {
        finalDiff = diffRes.diff;
      }
    }

    // ── Step 5: Build report ──────────────────────────────────────────────
    const testSummary = lastTestResult
      ? `\n\n## Test Verification\n- **Status**: ${lastTestResult.passed ? "✅ PASSED" : "❌ FAILED"}\n- **Attempts**: ${attemptsUsed}/${maxAttempts}\n- **Stack**: ${lastTestResult.stack}\n- **Stage**: ${lastTestResult.stage}`
      : "\n\n## Test Verification\n- **Status**: ⏭️ Skipped (no sandbox or no patch)";

    const firstLine = analysisText.split("\n").find((l) => l.trim()) || "See analysis for details";

    const proposal = `### 👻 Ghost Engineer: Incident Analysis & Fix Report

**Container**: \`${metadata.containerName}\`
**Image**: \`${metadata.image}\`
**Trigger**: ${metadata.action} (exit code: ${metadata.exitCode})
**Node**: ${metadata.nodeName}
**Attempts**: ${attemptsUsed}/${maxAttempts}

---

${analysisText}
${testSummary}

${finalDiff ? `\n## Final Patch\n\`\`\`diff\n${truncate(finalDiff, 5000)}\n\`\`\`` : ""}

---
**Action Required**: Review the above${lastTestResult?.passed ? " — tests passed ✅, ready to deploy" : " — tests failed or skipped, human review needed"}.`;

    await updateTaskProgress({
      tenantId: tenant_id,
      taskId: id,
      patch: {
        status: finalStatus,
        attempt_count: attemptsUsed,
        analysis_result: analysisText,
        result: {
          proposal,
          rootCause: firstLine,
          testPassed: lastTestResult?.passed ?? null,
          attemptsUsed,
          hasPatch: !!finalDiff,
        },
        progress_report: lastTestResult?.passed
          ? `✅ Tests passed after ${attemptsUsed} attempt(s). Patch ready.`
          : hasSandbox
            ? `Analysis complete. Tests ${lastTestResult ? "failed" : "not run"}. Human review required.`
            : "Analysis complete. No sandbox — patch not verified.",
      },
    });

    console.log(`[ghost-engineer] ✅ Task ${id} complete. testPassed=${lastTestResult?.passed ?? "N/A"} attempts=${attemptsUsed}`);

  } catch (err) {
    console.error(`[ghost-engineer] ❌ Task ${id} failed:`, err);
    await updateTaskProgress({
      tenantId: tenant_id,
      taskId: id,
      patch: {
        status: "failed",
        progress_report: String(err && err.message ? err.message : err),
      },
    });
  } finally {
    if (sandbox) {
      cleanupSandbox(sandbox);
    }
  }
}

module.exports = { runIncidentFixTask };