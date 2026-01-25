const fs = require("fs");
const os = require("os");
const path = require("path");
const { runCommand } = require("../utils/exec");

function mkSandboxDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "dfte-sandbox-"));
}

async function cloneRepo({ repoOwner, repoName, headSha, githubToken, useSsh, sshKeyContent, sshKeyPath }) {
  const rootDir = mkSandboxDir();
  const dir     = path.join(rootDir, "repo");
  fs.mkdirSync(dir, { recursive: true });

  let remote       = "";
  let gitSshCommand = "";

  if (useSsh && !githubToken) {
    remote = `git@github.com:${repoOwner}/${repoName}.git`;

    let finalKeyPath = sshKeyPath;
    if (sshKeyContent) {
      finalKeyPath = path.join(rootDir, "ssh_key");
      fs.writeFileSync(finalKeyPath, sshKeyContent, { mode: 0o600 });
    }
    if (finalKeyPath) {
      gitSshCommand = `ssh -i ${finalKeyPath} -o StrictHostKeyChecking=no`;
    }
  } else {
    // HTTPS với token — ưu tiên vì ổn định hơn SSH trong container
    remote = `https://x-access-token:${githubToken}@github.com/${repoOwner}/${repoName}.git`;
  }

  const env = { ...process.env };
  if (gitSshCommand) env.GIT_SSH_COMMAND = gitSshCommand;

  const cloneRes = await runCommand({
    command: "git",
    args: ["clone", "--no-checkout", "--depth", String(process.env.GIT_CLONE_DEPTH || 50), remote, dir],
    cwd: os.tmpdir(),
    timeoutMs: 5 * 60 * 1000,
    env,
  });
  if (cloneRes.exitCode !== 0) {
    throw new Error(`git clone failed: ${cloneRes.stderr || cloneRes.stdout}`);
  }

  // Checkout — thử main/master nếu không có headSha
  const checkoutTarget = headSha || "HEAD";
  let checkoutRes = await runCommand({
    command: "git",
    args: ["checkout", checkoutTarget],
    cwd: dir,
    timeoutMs: 2 * 60 * 1000,
    env,
  });

  if (checkoutRes.exitCode !== 0 && headSha) {
    // SHA không có trong shallow clone — fetch riêng
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
    checkoutRes = await runCommand({
      command: "git",
      args: ["checkout", headSha],
      cwd: dir,
      timeoutMs: 2 * 60 * 1000,
      env,
    });
    if (checkoutRes.exitCode !== 0) {
      throw new Error(`git checkout ${headSha} failed: ${checkoutRes.stderr || checkoutRes.stdout}`);
    }
  }

  // Git identity cho sandbox
  const gitName  = process.env.GIT_USER_NAME  || "Ghost Engineer";
  const gitEmail = process.env.GIT_USER_EMAIL || "ghost@nano.platform";
  await runCommand({ command: "git", args: ["config", "user.name",  gitName],  cwd: dir, env });
  await runCommand({ command: "git", args: ["config", "user.email", gitEmail], cwd: dir, env });

  return { dir, rootDir };
}

/**
 * Apply patch với 4 chiến lược theo thứ tự độ khắt khe giảm dần:
 *
 * 1. Strict:     --whitespace=nowarn               (nhanh nhất, đúng nhất)
 * 2. Lenient:    --ignore-whitespace --ignore-space-change  (bỏ qua whitespace diff)
 * 3. Fuzzy:      --ignore-whitespace -C0            (chấp nhận sai lệch ngữ cảnh)
 * 4. Ultra-Fuzzy: dùng lệnh 'patch' thay cho 'git apply' (cực kỳ linh hoạt với hunk headers)
 *
 * Trả về result của lần thành công đầu tiên, hoặc result lần cuối nếu tất cả fail.
 */
async function applyDiffFromFile({ repoDir, diffText }) {
  const diffFile = path.join(repoDir, "dfte.patch");

  // Normalize CRLF → LF trước khi write (git apply nhạy cảm với line endings)
  const normalized = diffText.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  fs.writeFileSync(diffFile, normalized, { encoding: "utf8" });

  // Thử git apply trước
  const gitStrategies = [
    ["apply", "--whitespace=nowarn", diffFile],
    ["apply", "--ignore-whitespace", "--ignore-space-change", "--whitespace=nowarn", diffFile],
    ["apply", "--ignore-whitespace", "-C0", "--whitespace=nowarn", diffFile],
  ];

  for (const args of gitStrategies) {
    const res = await runCommand({ command: "git", args, cwd: repoDir, timeoutMs: 2 * 60 * 1000 });
    if (res.exitCode === 0) {
      try { fs.unlinkSync(diffFile); } catch { /* ok */ }
      return res;
    }
    await runCommand({ command: "git", args: ["checkout", "--", "."], cwd: repoDir, timeoutMs: 30 * 1000 });
  }

  // Nếu git apply fail hết, thử dùng lệnh 'patch' (linh hoạt hơn với line numbers)
  const patchRes = await runCommand({
    command: "patch",
    args: ["-p1", "--ignore-whitespace", "-i", diffFile],
    cwd: repoDir,
    timeoutMs: 2 * 60 * 1000,
  });

  if (patchRes.exitCode === 0) {
    try { fs.unlinkSync(diffFile); } catch { /* ok */ }
    return patchRes;
  }

  try { fs.unlinkSync(diffFile); } catch { /* ok */ }
  return patchRes; // Trả về lỗi cuối cùng
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