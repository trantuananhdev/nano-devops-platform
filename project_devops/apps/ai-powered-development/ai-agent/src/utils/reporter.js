function exportTaskReport(task) {
  const { id, tenant_id, repo_owner, repo_name, pr_number, status, attempt_count, last_error, result, progress_report, logs, metadata, analysis_result } = task;

  const sections = [
    `# Task Report: ${id}`,
    `- **Tenant**: ${tenant_id}`,
    `- **Repo**: ${repo_owner}/${repo_name}#${pr_number}`,
    `- **Status**: ${status}`,
    `- **Attempts**: ${attempt_count}`,
    "",
    "## Progress Report",
    progress_report || "No progress reported yet.",
    "",
    "## Analysis Result",
    analysis_result || "Analysis not performed yet.",
    "",
    "## Summary",
    last_error ? `Last error: ${last_error}` : "Task completed successfully or is in progress.",
    "",
    "## Logs",
    logs ? "```\n" + logs + "\n```" : "No logs available.",
    "",
    "## Result",
    result && result.outputMarkdown ? result.outputMarkdown : "No output generated yet.",
    "",
    "---",
    `Report generated at: ${new Date().toISOString()}`,
  ];

  return sections.join("\n");
}

module.exports = { exportTaskReport };
