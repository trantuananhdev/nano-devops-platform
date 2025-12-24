const { getTenantsWithQueuedTasks, claimNextQueuedTask, updateTaskProgress } = require("../adapters/db/taskRepo");
const { findTenantByRepoFullName } = require("../adapters/db/githubRepoMappingRepo");
const { runGithubPrDevTask } = require("../tasks/githubPrDevTask");
const { runIncidentFixTask } = require("../tasks/incidentFixTask");

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function startTaskWorker() {
  // eslint-disable-next-line no-console
  console.log("[dfte] worker started (polling DB)");

  const tick = async () => {
    try {
      const tenants = await getTenantsWithQueuedTasks();
      if (!tenants.length) return;

      for (const tenantId of tenants.slice(0, 10)) {
        const task = await claimNextQueuedTask({ tenantId });
        if (!task) continue;

        // Route task to appropriate handler based on taskType
        if (task.task_type === "github_pr_dev") {
          runGithubPrDevTask(task).catch((err) => {
            // eslint-disable-next-line no-console
            console.error("[dfte] PR task failed", { taskId: task.id, error: err && err.message ? err.message : err });
          });
        } else if (task.task_type === "incident_fix") {
          runIncidentFixTask(task).catch((err) => {
            // eslint-disable-next-line no-console
            console.error("[dfte] incident fix task failed", { taskId: task.id, error: err && err.message ? err.message : err });
          });
        }
      }
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("[dfte] worker tick error", err && err.message ? err.message : err);
    }
  };

  // Poll interval: 10s for MVP.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    await tick();
    await sleep(10000);
  }
}

module.exports = { startTaskWorker };

