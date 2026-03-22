const fs = require("fs");
const os = require("os");
const path = require("path");
const { runCommand } = require("../utils/exec");

function mkSandboxDir() {
  const base = os.tmpdir();
  return fs.mkdtempSync(path.join(base, "dfte-sandbox-"));
}

async function cloneRepo({ repoOwner, repoName, headSha, githubToken, useSsh, sshKeyContent, sshKeyPath }) {
  const rootDir = mkSandboxDir();
  const dir = path.join(rootDir, "repo");
  fs.mkdirSync(dir, { recursive: true });

  let remote = "";
  let gitSshCommand = "";

  if (useSsh) {
    remote = `git@github.com:${repoOwner}/${repoName}.git`;
    
    // If raw content provided, write to a temporary file
    let finalKeyPath = sshKeyPath;
    if (sshKeyContent) {
      finalKeyPath = path.join(rootDir, "ssh_key");
      fs.writeFileSync(finalKeyPath, sshKeyContent, { mode: 0o600 });
    }

    if (finalKeyPath) {
      gitSshCommand = `ssh -i ${finalKeyPath} -o StrictHostKeyChecking=no`;
    }
  } else {
    remote = `https://x-access-token:${githubToken}@github.com/${repoOwner}/${repoName}.git`;
  }

  const env = { ...process.env };
  if (gitSshCommand) {
    env.GIT_SSH_COMMAND = gitSshCommand;
  }

  const cloneRes = await runCommand({
    command: "git",
    args: ["clone", "--no-checkout", "--depth", String(process.env.GIT_CLONE_DEPTH || 200), remote, dir],
    cwd: os.tmpdir(),
    timeoutMs: 5 * 60 * 1000,
    env,
  });
  if (cloneRes.exitCode !== 0) {
    throw new Error(`git clone failed: ${cloneRes.stderr || cloneRes.stdout}`);
  }

  const checkoutArgs = headSha ? ["checkout", headSha] : ["checkout", "main"];

  let checkoutRes = await runCommand({
    command: "git",
    args: checkoutArgs,
    cwd: dir,
    timeoutMs: 2 * 60 * 1000,
    env,
  });

  if (checkoutRes.exitCode !== 0 && headSha) {
    // If depth didn't include the SHA, fetch that specific commit.
    const fetchRes = await runCommand({
      command: "git",
      args: ["fetch", "--depth", "1", "origin", headSha],
      cwd: dir,
      timeoutMs: 2 * 60 * 1000,
      env,
    });
    if (fetchRes.exitCode !== 0) {
      throw new Error(`git fetch ${headSha} failed: ${fetchRes.stderr || fetchRes.stdout}`);
    }
    checkoutRes = await runCommand({ command: "git", args: ["checkout", headSha], cwd: dir, timeoutMs: 2 * 60 * 1000, env });
    if (checkoutRes.exitCode !== 0) {
      throw new Error(`git checkout ${headSha} failed: ${checkoutRes.stderr || checkoutRes.stdout}`);
    }
  }

  // Configure Git identity for this sandbox
  const gitName = process.env.GIT_USER_NAME || "Ghost Engineer";
  const gitEmail = process.env.GIT_USER_EMAIL || "ghost@nano.platform";
  await runCommand({ command: "git", args: ["config", "user.name", gitName], cwd: dir, env });
  await runCommand({ command: "git", args: ["config", "user.email", gitEmail], cwd: dir, env });

  return { dir, rootDir };
}

async function applyDiffFromFile({ repoDir, diffText }) {
  const diffFile = path.join(repoDir, "dfte.patch");
  fs.writeFileSync(diffFile, diffText, "utf8");
  const res = await runCommand({
    command: "git",
    args: ["apply", "--whitespace=nowarn", diffFile],
    cwd: repoDir,
    timeoutMs: 2 * 60 * 1000,
  });
  fs.unlinkSync(diffFile);
  return res;
}

async function getWorkingDiff({ repoDir }) {
  const res = await runCommand({
    command: "git",
    args: ["diff", "HEAD"],
    cwd: repoDir,
    timeoutMs: 2 * 60 * 1000,
  });
  return { exitCode: res.exitCode, diff: res.stdout };
}

function cleanupSandbox({ rootDir }) {
  try {
    fs.rmSync(rootDir, { recursive: true, force: true });
  } catch {
    // ignore
  }
}

module.exports = {
  cloneRepo,
  applyDiffFromFile,
  getWorkingDiff,
  cleanupSandbox,
};

