const { spawn } = require("child_process");

function truncate(s, maxChars) {
  if (!s) return "";
  if (s.length <= maxChars) return s;
  return s.slice(0, maxChars) + `\n...<truncated ${s.length - maxChars} chars>...`;
}

async function runCommand({ command, args, cwd, env, timeoutMs }) {
  const proc = spawn(command, args, {
    cwd,
    env: { ...process.env, ...(env || {}) },
    stdio: ["ignore", "pipe", "pipe"],
    shell: false,
  });

  let stdout = "";
  let stderr = "";

  proc.stdout.on("data", (d) => {
    stdout += d.toString("utf8");
  });
  proc.stderr.on("data", (d) => {
    stderr += d.toString("utf8");
  });

  const timeout = timeoutMs
    ? setTimeout(() => {
        proc.kill("SIGKILL");
      }, timeoutMs)
    : null;

  const exitCode = await new Promise((resolve) => {
    proc.on("close", (code) => resolve(code));
  });
  if (timeout) clearTimeout(timeout);

  return {
    exitCode,
    stdout: truncate(stdout, Number(process.env.LOG_TRIM_CHARS || 20000)),
    stderr: truncate(stderr, Number(process.env.LOG_TRIM_CHARS || 20000)),
  };
}

module.exports = { runCommand };

