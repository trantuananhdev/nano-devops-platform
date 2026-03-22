const fs = require("fs");
const path = require("path");
const { runCommand } = require("../utils/exec");

/**
 * Detects the project stack based on files in the repository.
 * Returns { stack: 'node'|'go'|'python'|'unknown', manager: string, testCommand: string[] }
 */
function detectProjectStack(repoDir) {
  const has = (name) => fs.existsSync(path.join(repoDir, name));

  // Node.js
  if (has("package.json")) {
    let manager = "npm";
    if (has("pnpm-lock.yaml")) manager = "pnpm";
    else if (has("yarn.lock")) manager = "yarn";
    return { stack: "node", manager, testCommand: [manager, "test"] };
  }

  // Go
  if (has("go.mod")) {
    return { stack: "go", manager: "go", testCommand: ["go", "test", "./..."] };
  }

  // Python
  if (has("requirements.txt") || has("pyproject.toml") || has("setup.py")) {
    let manager = "pip";
    if (has("poetry.lock")) manager = "poetry";
    else if (has("Pipfile")) manager = "pipenv";
    
    const testCmd = manager === "poetry" ? ["poetry", "run", "pytest"] : ["pytest"];
    return { stack: "python", manager, testCommand: testCmd };
  }

  return { stack: "unknown", manager: "unknown", testCommand: [] };
}

async function ensureDependencies({ repoDir, stack, manager }) {
  const timeoutMs = 10 * 60 * 1000;

  if (stack === "node") {
    if (manager === "npm") {
      const args = fs.existsSync(path.join(repoDir, "package-lock.json")) ? ["ci"] : ["install"];
      const res = await runCommand({ command: "npm", args, cwd: repoDir, timeoutMs });
      return { ok: res.exitCode === 0, ...res };
    }
    const res = await runCommand({
      command: manager,
      args: ["install", "--frozen-lockfile"],
      cwd: repoDir,
      timeoutMs,
    });
    return { ok: res.exitCode === 0, ...res };
  }

  if (stack === "go") {
    const res = await runCommand({ command: "go", args: ["mod", "download"], cwd: repoDir, timeoutMs });
    return { ok: res.exitCode === 0, ...res };
  }

  if (stack === "python") {
    if (manager === "poetry") {
      const res = await runCommand({ command: "poetry", args: ["install"], cwd: repoDir, timeoutMs });
      return { ok: res.exitCode === 0, ...res };
    }
    // Default pip
    const res = await runCommand({ command: "pip", args: ["install", "-r", "requirements.txt"], cwd: repoDir, timeoutMs });
    return { ok: res.exitCode === 0, ...res };
  }

  return { ok: true, stdout: "No dependencies to install for unknown stack", stderr: "", exitCode: 0 };
}

async function runTestCommand({ repoDir, stack, testCommand }) {
  const testTimeoutMs = Number(process.env.TEST_TIMEOUT_MS || 10 * 60 * 1000);

  if (stack === "unknown" || testCommand.length === 0) {
    return { exitCode: 1, stdout: "", stderr: "Could not detect how to run tests for this project." };
  }

  const [cmd, ...args] = testCommand;
  const res = await runCommand({ command: cmd, args, cwd: repoDir, timeoutMs: testTimeoutMs });
  return res;
}

async function runTestsVerified({ repoDir, skipInstall = false }) {
  const { stack, manager, testCommand } = detectProjectStack(repoDir);

  if (!skipInstall && stack !== "unknown") {
    const depRes = await ensureDependencies({ repoDir, stack, manager });
    if (!depRes.ok) {
      return {
        passed: false,
        stack,
        manager,
        testCommand,
        stage: "dependencies",
        exitCode: depRes.exitCode,
        stdout: depRes.stdout,
        stderr: depRes.stderr,
      };
    }
  }

  const testRes = await runTestCommand({ repoDir, stack, testCommand });
  return {
    passed: testRes.exitCode === 0,
    stack,
    manager,
    testCommand,
    stage: "tests",
    exitCode: testRes.exitCode,
    stdout: testRes.stdout,
    stderr: testRes.stderr,
  };
}

module.exports = { runTestsVerified };

