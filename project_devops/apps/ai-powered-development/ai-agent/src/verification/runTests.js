const fs = require("fs");
const path = require("path");
const { runCommand } = require("../utils/exec");

// ─────────────────────────────────────────────
// Priority 1: ghost-engineer.json trong repo
// Dev tự khai báo cách build + test.
//
// Ví dụ cho các stack phổ biến:
//
// Java Maven:
// { "stack": "java", "install": ["mvn", "dependency:resolve", "-q"], "test": ["mvn", "test", "-q"] }
//
// React (không có unit test):
// { "stack": "react", "install": ["npm", "install"], "test": ["npm", "run", "build"] }
//
// Không cần verify gì — accept mọi patch:
// { "stack": "legacy", "install": [], "test": [] }
// ─────────────────────────────────────────────

function loadGhostConfig(repoDir) {
  const p = path.join(repoDir, "ghost-engineer.json");
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

// ─────────────────────────────────────────────
// Priority 2: Auto-detect
// Support: Node.js, Python, Java (Maven/Gradle), PHP
// ─────────────────────────────────────────────

function readPackageJson(repoDir) {
  try {
    return JSON.parse(fs.readFileSync(path.join(repoDir, "package.json"), "utf8"));
  } catch {
    return null;
  }
}

function detectStack(repoDir) {
  const has = (name) => fs.existsSync(path.join(repoDir, name));
  const pkg = readPackageJson(repoDir);

  // ── Node.js ──────────────────────────────────────────────────────────────
  if (has("package.json")) {
    const mgr = has("pnpm-lock.yaml") ? "pnpm" : has("yarn.lock") ? "yarn" : "npm";
    const installCmd = mgr === "npm" ? ["npm", "install"] : [mgr, "install"];

    const hasRealTest = pkg && pkg.scripts && pkg.scripts.test &&
      !String(pkg.scripts.test).includes("no test specified") &&
      !String(pkg.scripts.test).includes("echo");

    let testCmd;
    if (hasRealTest) {
      testCmd = [mgr, "test"];
    } else if (has("vitest.config.js") || has("vitest.config.ts")) {
      testCmd = ["npx", "vitest", "run", "--reporter=verbose"];
    } else if (has("jest.config.js") || has("jest.config.ts") || has("jest.config.json")) {
      testCmd = ["npx", "jest", "--forceExit"];
    } else if (pkg && pkg.scripts && pkg.scripts.build) {
      testCmd = [mgr, "run", "build"]; // fallback: build check
    } else {
      testCmd = null;
    }

    return { stack: "nodejs", manager: mgr, installCommand: installCmd, testCommand: testCmd };
  }

  // ── Python ───────────────────────────────────────────────────────────────
  if (has("requirements.txt") || has("pyproject.toml") || has("setup.py") || has("Pipfile")) {
    let mgr = "pip";
    if (has("poetry.lock") || (has("pyproject.toml") && !has("setup.py"))) mgr = "poetry";
    else if (has("Pipfile")) mgr = "pipenv";

    const installCmd = mgr === "poetry"
      ? ["poetry", "install", "--no-interaction", "--no-root"]
      : mgr === "pipenv"
        ? ["pipenv", "install"]
        : ["pip", "install", "-r", "requirements.txt", "-q"];

    const hasPytest = has("pytest.ini") || has("conftest.py") ||
      has("tests") || has("test") || has("tests/__init__.py");

    const testCmd = hasPytest
      ? (mgr === "poetry"
          ? ["poetry", "run", "pytest", "-q", "--tb=short"]
          : ["pytest", "-q", "--tb=short"])
      : ["python", "-m", "compileall", "-q", "."]; // fallback: syntax check

    return { stack: "python", manager: mgr, installCommand: installCmd, testCommand: testCmd };
  }

  // ── Java / Maven ─────────────────────────────────────────────────────────
  if (has("pom.xml")) {
    const mvn = has("mvnw") ? "./mvnw" : "mvn";
    const FLAGS = ["-q", "--no-transfer-progress", "-B"];
    const installCmd = [mvn, "dependency:resolve", ...FLAGS];
    const testCmd = has("src/test")
      ? [mvn, "test", ...FLAGS]
      : [mvn, "compile", ...FLAGS]; // fallback: compile check
    return { stack: "java-maven", manager: mvn, installCommand: installCmd, testCommand: testCmd };
  }

  // ── Java / Gradle ────────────────────────────────────────────────────────
  if (has("build.gradle") || has("build.gradle.kts")) {
    const gradle = has("gradlew") ? "./gradlew" : "gradle";
    const installCmd = [gradle, "dependencies", "-q"];
    const testCmd = has("src/test")
      ? [gradle, "test", "-q"]
      : [gradle, "build", "-x", "test", "-q"]; // fallback: build check
    return { stack: "java-gradle", manager: gradle, installCommand: installCmd, testCommand: testCmd };
  }

  // ── PHP / Composer ───────────────────────────────────────────────────────
  if (has("composer.json")) {
    const installCmd = ["composer", "install", "--quiet", "--no-interaction", "--no-scripts"];

    let testCmd;
    if (has("phpunit.xml") || has("phpunit.xml.dist")) {
      testCmd = ["./vendor/bin/phpunit", "--no-coverage", "--colors=never"];
    } else if (has("tests/Pest.php") || has("pest.php")) {
      testCmd = ["./vendor/bin/pest", "--no-coverage"];
    } else {
      // Fallback: syntax check tất cả .php files
      testCmd = ["find", ".", "-name", "*.php", "-not", "-path", "*/vendor/*",
        "-exec", "php", "-l", "{}", "+"];
    }

    return { stack: "php", manager: "composer", installCommand: installCmd, testCommand: testCmd };
  }

  return { stack: "unknown", manager: "unknown", installCommand: null, testCommand: null };
}

// ─────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────

async function runTestsVerified({ repoDir, skipInstall = false }) {
  const timeoutInstall = Number(process.env.INSTALL_TIMEOUT_MS || 5 * 60 * 1000);
  const timeoutTest    = Number(process.env.TEST_TIMEOUT_MS    || 10 * 60 * 1000);

  // ── Priority 1: ghost-engineer.json ──────────────────────────────────────
  const ghostConfig = loadGhostConfig(repoDir);
  if (ghostConfig) {
    console.log(`[runTests] ghost-engineer.json (stack: ${ghostConfig.stack})`);

    if (!skipInstall && Array.isArray(ghostConfig.install) && ghostConfig.install.length > 0) {
      const [cmd, ...args] = ghostConfig.install;
      const res = await runCommand({ command: cmd, args, cwd: repoDir, timeoutMs: timeoutInstall });
      if (res.exitCode !== 0) {
        return makeResult({ passed: false, stage: "dependencies", stack: ghostConfig.stack, manager: ghostConfig.stack, testCommand: ghostConfig.install, res });
      }
    }

    if (!Array.isArray(ghostConfig.test) || ghostConfig.test.length === 0) {
      return makeResult({
        passed: true, stage: "no-test", stack: ghostConfig.stack, manager: ghostConfig.stack, testCommand: [],
        res: { exitCode: 0, stdout: "No test in ghost-engineer.json — patch accepted.", stderr: "" },
      });
    }

    const [cmd, ...args] = ghostConfig.test;
    const res = await runCommand({ command: cmd, args, cwd: repoDir, timeoutMs: timeoutTest });
    return makeResult({ passed: res.exitCode === 0, stage: "tests", stack: ghostConfig.stack, manager: ghostConfig.stack, testCommand: ghostConfig.test, res });
  }

  // ── Priority 2: Auto-detect ───────────────────────────────────────────────
  const { stack, manager, installCommand, testCommand } = detectStack(repoDir);
  console.log(`[runTests] auto-detect stack=${stack} manager=${manager}`);

  if (stack === "unknown") {
    return makeResult({
      passed: true, stage: "no-test", stack, manager, testCommand: [],
      res: {
        exitCode: 0,
        stdout: "Stack not recognized. Patch accepted without verification. Add ghost-engineer.json to configure tests.",
        stderr: "",
      },
    });
  }

  // Install
  if (!skipInstall && installCommand) {
    const [cmd, ...args] = installCommand;
    const res = await runCommand({ command: cmd, args, cwd: repoDir, timeoutMs: timeoutInstall });
    if (res.exitCode !== 0) {
      return makeResult({ passed: false, stage: "dependencies", stack, manager, testCommand: installCommand, res });
    }
  }

  // No test — accept patch
  if (!testCommand) {
    return makeResult({
      passed: true, stage: "no-test", stack, manager, testCommand: [],
      res: {
        exitCode: 0,
        stdout: `No test suite found for ${stack}. Patch accepted. Add ghost-engineer.json to configure tests.`,
        stderr: "",
      },
    });
  }

  // Run tests
  const [cmd, ...args] = testCommand;
  const res = await runCommand({ command: cmd, args, cwd: repoDir, timeoutMs: timeoutTest });
  return makeResult({ passed: res.exitCode === 0, stage: "tests", stack, manager, testCommand, res });
}

function makeResult({ passed, stage, stack, manager, testCommand, res }) {
  return { passed, stage, stack, manager, testCommand, exitCode: res.exitCode, stdout: res.stdout, stderr: res.stderr };
}

module.exports = { runTestsVerified, detectStack, loadGhostConfig };