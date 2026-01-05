const path = require("path");
const { findTenantByRepoFullName } = require("../adapters/db/githubRepoMappingRepo");
const { createLlmProvider } = require("../llm/providerFactory");
const { createGithubConnector } = require("../connectors/github/githubConnector");
const { runTestsVerified } = require("../verification/runTests");
const { cloneRepo, applyDiffFromFile, getWorkingDiff, cleanupSandbox } = require("../sandbox/repoSandbox");
const { updateTaskProgress } = require("../adapters/db/taskRepo");
const { addLessonIfPass, addPattern, getTenantMemory } = require("../adapters/db/tenantMemoryPg");
const { extractUnifiedDiff } = require("./extractUnifiedDiff");

function buildSystemPrompt({ patterns = [] } = {}) {
  const patternSection = patterns.length
    ? `\nPreviously learned patterns to follow:\n${patterns.map((p) => `- ${p.title}: ${p.content}`).join("\n")}`
    : "";

  return [
    "You are an AI Dev Agent that must fix a GitHub Pull Request so that tests pass.",
    "Rules:",
    "- Output ONLY a single unified diff inside a code block labeled `diff`.",
    "- Do not add explanations outside the diff.",
    "- Do not use probabilistic language. If you cannot produce a patch, output an empty diff block.",
    patternSection,
  ].join("\n");
}

function buildCoderPrompt({ pr, files, failing, attemptNo, maxAttempts, currentDiff, stack, manager, testCommand }) {
  const fileSection = files
    .map((f) => `File: ${f.filename}\nStatus: ${f.status}\n\n${f.content}`)
    .join("\n\n---\n\n");

  const currentDiffSection = currentDiff && currentDiff.trim() ? `\nCurrent working diff:\n${currentDiff}` : "";

  return [
    `Attempt ${attemptNo} / ${maxAttempts}`,
    "",
    `Project Stack: ${stack} (Manager: ${manager})`,
    `Test Command: ${testCommand.join(" ")}`,
    "",
    `PR title: ${pr.title || "(no title)"}`,
    `PR body (short): ${(pr.body || "").slice(0, 800)}`,
    "",
    "Changed files (head contents):",
    fileSection || "(no changed file contents available)",
    "",
    "Verification gate result (failing):",
    "Exit code != 0. Test logs (truncated):",
    `${failing.stderr || ""}\n${failing.stdout || ""}`.trim(),
    currentDiffSection,
    "",
    "Task:",
    `Produce a patch that makes \`${testCommand.join(" ")}\` pass.`,
    "If new tests are needed, add them.",
  ].join("\n");
}

function buildCommentBody({ status, attempts, failingSummary, finalTest, finalDiff }) {
  if (status === "completed") {
    return [
      "## AI Dev Agent: Verification passed",
      `Attempts: ${attempts}`,
      "",
      "### Evidence",
      `- Test stage: ${finalTest.stage}`,
      `- Exit code: ${finalTest.exitCode}`,
      "",
      "### Patch (unified diff)",
      "```diff",
      finalDiff || "(no diff changes detected)",
      "```",
    ].join("\n");
  }

  return [
    "## AI Dev Agent: Verification failed",
    `Attempts: ${attempts}`,
    "",
    "### Evidence (last attempt)",
    `- Stage: ${finalTest.stage}`,
    `- Exit code: ${finalTest.exitCode}`,
    "",
    "### Last error summary",
    failingSummary || "(no summary)",
    "",
    "### Patch (unified diff)",
    "```diff",
    finalDiff || "(no diff changes detected)",
    "```",
    "",
    "### 🔍 Human Review Guide",
    "Verification failed after max attempts. To proceed:",
    "1. Review the patch above for correctness.",
    "2. Check the test logs in the system dashboard.",
    "3. Apply manually if valid, or refine the PR description to provide more context for the AI Agent.",
  ].join("\n");
}

function truncateForOutput(text, maxChars) {
  if (!text) return "";
  if (text.length <= maxChars) return text;
  return text.slice(0, maxChars) + `\n...<truncated ${text.length - maxChars} chars>...`;
}

async function runGithubPrDevTask(task) {
  const tenantId = task.tenant_id;
  const taskId = task.id;
  const repoOwner = task.repo_owner;
  const repoName = task.repo_name;
  const prNumber = task.pr_number;
  const headSha = task.pr_head_sha;
  const maxAttempts = task.max_attempts || 3;

  let sandbox = null;
  try {
    await updateTaskProgress({
      tenantId,
      taskId,
      patch: { last_error: null },
    });

    const repoFullName = `${repoOwner}/${repoName}`;
    const tenantRow = await findTenantByRepoFullName({ repoFullName });
    if (!tenantRow) throw new Error(`No github credential mapping for ${repoFullName}`);

    const githubToken = tenantRow.github_token;
    const github = createGithubConnector({ githubToken });
    const llm = createLlmProvider();
    const memory = await getTenantMemory(tenantId);
    const patterns = Array.isArray(memory?.patterns) ? memory.patterns : [];

    // 1) Clone + checkout PR head
    const useSsh = !!tenantRow.ssh_key || !!process.env.GITHUB_SSH_KEY_FILE;
    sandbox = await cloneRepo({
      repoOwner,
      repoName,
      headSha,
      githubToken,
      useSsh,
      sshKeyContent: tenantRow.ssh_key,
      sshKeyPath: process.env.GITHUB_SSH_KEY_FILE,
    });

    // 2) Fetch PR context (title/body + changed files)
    const pr = await github.getPullRequest({ owner: repoOwner, repo: repoName, pullNumber: prNumber });
    const filesMeta = await github.listPullRequestFiles({ owner: repoOwner, repo: repoName, pullNumber: prNumber, limitFiles: 10 });

    // Pull head contents for each changed file (limit size)
    const maxFileChars = Number(process.env.MAX_FILE_CHARS || 2000);
    const files = [];
    for (const f of filesMeta) {
      try {
        if (f.status === "removed") {
          files.push({ filename: f.filename, status: f.status, content: "(file removed in PR)" });
          continue;
        }
        const content = await github.getFileContent({ owner: repoOwner, repo: repoName, path: f.filename, ref: headSha });
        files.push({
          filename: f.filename,
          status: f.status,
          content: content ? content.slice(0, maxFileChars) : "(no file content)",
        });
      } catch {
        files.push({ filename: f.filename, status: f.status, content: "(file content fetch failed)" });
      }
    }

    // 3) Verification loop: run tests -> ask LLM for patch -> apply -> re-run tests
    let attemptNo = 0;
    let attemptsUsed = 0;
    let lastVerification = null;
    let finalDiff = "";
    let lastLlmFeedback = null;
    let depsInstalled = false;

    for (; attemptNo < maxAttempts; attemptNo += 1) {
      const nextAttemptNo = attemptNo + 1;
      attemptsUsed = nextAttemptNo;
      await updateTaskProgress({ tenantId, taskId, patch: { attempt_count: nextAttemptNo, last_error: null } });

      lastVerification = await runTestsVerified({ repoDir: sandbox.dir, skipInstall: depsInstalled });
      if (lastVerification.stage === "dependencies" && lastVerification.passed === false) {
        // failed install
      } else {
        depsInstalled = true; // Mark as installed if we got past dependency stage
      }
      finalDiff = await getWorkingDiff({ repoDir: sandbox.dir }).then((r) => (r.exitCode === 0 ? r.diff : ""));

      if (lastVerification.passed) {
        // Verified done.
        break;
      }

      if (nextAttemptNo >= maxAttempts) break;

      const currentDiff = finalDiff;
      const systemPrompt = buildSystemPrompt({ patterns });
      let coderPrompt = buildCoderPrompt({
        pr,
        files,
        failing: lastVerification,
        attemptNo: nextAttemptNo,
        maxAttempts,
        currentDiff,
        stack: lastVerification.stack,
        manager: lastVerification.manager,
        testCommand: lastVerification.testCommand,
      });

      if (lastLlmFeedback) {
        coderPrompt = `${lastLlmFeedback}\n\n${coderPrompt}`;
        lastLlmFeedback = null;
      }

      const llmText = await llm.chatText({
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: coderPrompt },
        ],
      });

      const diffText = extractUnifiedDiff(llmText);
      if (!diffText) {
        await updateTaskProgress({
          tenantId,
          taskId,
          patch: { last_error: "LLM did not return a diff patch" },
        });
        continue;
      }

      const applyRes = await applyDiffFromFile({ repoDir: sandbox.dir, diffText });
      if (applyRes.exitCode !== 0) {
        await updateTaskProgress({
          tenantId,
          taskId,
          patch: { last_error: `git apply failed: ${applyRes.stderr || applyRes.stdout}` },
        });
        // Let loop retry with updated error logs on next iteration.
        lastVerification = {
          ...lastVerification,
          passed: false,
          stage: "git_apply",
          exitCode: applyRes.exitCode,
          stderr: applyRes.stderr,
          stdout: applyRes.stdout,
        };
        continue;
      }
    }

    // 4) Final verification (best effort)
    const finalTest = await runTestsVerified({ repoDir: sandbox.dir });
    finalDiff = await getWorkingDiff({ repoDir: sandbox.dir }).then((r) => (r.exitCode === 0 ? r.diff : ""));
    const maxDiffChars = Number(process.env.MAX_DIFF_CHARS || 20000);
    const diffForComment = truncateForOutput(finalDiff, maxDiffChars);

    const status = finalTest.passed ? "completed" : "failed";
    const failingSummary = `${finalTest.stderr ? finalTest.stderr.slice(0, 800) : ""}`.trim();

    const commentBody = buildCommentBody({
      status,
      attempts: attemptsUsed,
      failingSummary,
      finalTest,
      finalDiff: diffForComment,
    });

    await github.commentOnPullRequest({ owner: repoOwner, repo: repoName, pullNumber: prNumber, body: commentBody });

    await updateTaskProgress({
      tenantId,
      taskId,
      patch: {
        status: status === "completed" ? "completed" : "failed",
        result: {
          repoFullName,
          prNumber,
          prHeadSha: headSha,
          attempts: attemptsUsed,
          verification: finalTest,
        },
      },
    });

    if (finalTest.passed) {
      // Record evolution
      const lesson = {
        title: `Fixed PR ${repoOwner}/${repoName}#${prNumber}`,
        evidence: [`Verification passed after ${attemptsUsed} attempts.`],
        createdAt: new Date().toISOString(),
      };
      await addLessonIfPass({ tenantId, lesson });

      // If it was hard (more than 1 attempt), extract a pattern
      if (attemptsUsed > 1) {
        await addPattern({
          tenantId,
          pattern: {
            title: `Fix for ${repoOwner}/${repoName}`,
            content: `The issue required ${attemptsUsed} attempts. Check diff for patterns in ${files.map((f) => f.filename).join(", ")}.`,
            createdAt: new Date().toISOString(),
          },
        });
      }
    }
  } catch (err) {
    const msg = String(err && err.message ? err.message : err);
    await updateTaskProgress({
      tenantId: task.tenant_id,
      taskId: task.id,
      patch: { status: "error", last_error: msg, result: { error: msg } },
    });
    throw err;
  } finally {
    if (sandbox) cleanupSandbox({ rootDir: sandbox.rootDir });
  }
}

module.exports = { runGithubPrDevTask };

