const { updateTaskProgress } = require("../adapters/db/taskRepo");
const { createLlmProvider } = require("../llm/providerFactory");
const { findTenantByRepoFullName } = require("../adapters/db/githubRepoMappingRepo");
const { cloneRepo, cleanupSandbox } = require("../sandbox/repoSandbox");
const fs = require("fs");
const path = require("path");

async function runIncidentFixTask(task) {
  const { id, tenant_id, metadata, logs, repo_owner, repo_name } = task;

  console.log(`[ghost-engineer] 👻 Analyzing incident for task ${id}...`);

  let sandbox = null;
  try {
    await updateTaskProgress({
      tenantId: tenant_id,
      taskId: id,
      patch: { status: "running", progress_report: "Ghost Engineer is investigating the scene..." },
    });

    // Guard: metadata và logs phải có
    const parsedMetadata = typeof metadata === "string" ? JSON.parse(metadata) : metadata;
    if (!parsedMetadata || !logs) {
      throw new Error("Missing metadata or logs in task payload");
    }

    // Attempt to clone repo to get code context
    let codeContext = "";
    const repoFullName = `${repo_owner}/${repo_name}`;
    if (repo_owner !== "unknown") {
      try {
        const tenantRow = await findTenantByRepoFullName({ repoFullName });
        if (tenantRow) {
          console.log(`[ghost-engineer] Cloning ${repoFullName} for code context...`);
          sandbox = await cloneRepo({
            repoOwner: repo_owner,
            repoName: repo_name,
            githubToken: tenantRow.github_token,
            useSsh: !!tenantRow.ssh_key || !!process.env.GITHUB_SSH_KEY_FILE,
            sshKeyContent: tenantRow.ssh_key,
            sshKeyPath: process.env.GITHUB_SSH_KEY_FILE,
          });

          // Read relevant files (server.js is usually a good start for this demo)
          const serverJsPath = path.join(sandbox.dir, "server.js");
          if (fs.existsSync(serverJsPath)) {
            codeContext = `\nRelevant source code from server.js:\n---\n${fs.readFileSync(serverJsPath, "utf8")}\n---`;
          }
        }
      } catch (cloneErr) {
        console.warn(`[ghost-engineer] Could not clone repo for context: ${cloneErr.message}`);
      }
    }

    const llm = createLlmProvider();

    const prompt = `You are "The Ghost Engineer", an autonomous SRE and Developer.
An incident occurred in the container "${parsedMetadata.containerName}" (Image: ${parsedMetadata.image}).
Action: ${parsedMetadata.action}
Exit Code: ${parsedMetadata.exitCode}

Here are the last 100 lines of logs:
---
${logs}
---
${codeContext}

Your task:
1. Analyze the logs and code to identify the root cause.
2. Provide a clear, concise explanation of what went wrong.
3. Suggest a specific code fix with a before/after code snippet.
4. Format your response in Markdown.

BE CONCISE AND PROFESSIONAL.`;

    const analysis = await llm.chatText({
      messages: [
        { role: "system", content: "You are The Ghost Engineer, a senior SRE/DevOps expert." },
        { role: "user", content: prompt },
      ],
    });

    const firstLine = analysis.split("\n").find((l) => l.trim()) || "See analysis for details";

    const mrProposal = `### 👻 Ghost Engineer: Incident Analysis Report

**Container**: \`${metadata.containerName}\`
**Image**: \`${metadata.image}\`
**Trigger**: ${metadata.action} (exit code: ${metadata.exitCode})
**Node**: ${metadata.nodeName}

---

${analysis}

---
**Verification Status**: 🟢 Analyzed by Ghost Engineer  
**Action Required**: Review the above and click **Approve** to deploy the suggested fix.`;

    await updateTaskProgress({
      tenantId: tenant_id,
      taskId: id,
      patch: {
        status: "completed",
        analysis_result: analysis,
        result: { proposal: mrProposal, rootCause: firstLine },
        progress_report: "Analysis complete. Report generated.",
      },
    });

    console.log(`[ghost-engineer] ✅ Analysis complete for task ${id}.`);
  } catch (err) {
    console.error(`[ghost-engineer] ❌ Failed to process incident task ${id}:`, err);
    await updateTaskProgress({
      tenantId: tenant_id,
      taskId: id,
      patch: { status: "failed", progress_report: String(err && err.message ? err.message : err) },
    });
  } finally {
    if (sandbox) {
      cleanupSandbox(sandbox);
    }
  }
}

module.exports = { runIncidentFixTask };