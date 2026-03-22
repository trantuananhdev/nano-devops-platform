const { signAccessToken, verifyAccessToken } = require("../auth/jwt");
const { extractUnifiedDiff } = require("../tasks/extractUnifiedDiff");
const { findForbiddenLanguage } = require("../tasks/outputGuards");

async function main() {
  process.env.JWT_SECRET = process.env.JWT_SECRET || "smoke-secret";

  // JWT sanity check
  const token = signAccessToken({ tenantId: "t1", userId: "u1", role: "admin" });
  const decoded = verifyAccessToken(token);
  if (!decoded || decoded.tenant_id !== "t1" || decoded.sub !== "u1" || decoded.role !== "admin") {
    throw new Error("JWT verification failed");
  }

  // Diff extraction sanity check
  const sample = "Here\n```diff\n--- a/a.txt\n+++ b/a.txt\n@@\n-foo\n+bar\n```\n";
  const diff = extractUnifiedDiff(sample);
  if (!diff || !diff.includes("--- a/a.txt") || !diff.includes("+bar")) {
    throw new Error("extractUnifiedDiff failed");
  }

  // Forbidden language guard sanity check
  const hits = findForbiddenLanguage("This should pass. Diff below.");
  if (!hits.length) throw new Error("Forbidden language guard did not detect");

  // eslint-disable-next-line no-console
  console.log("SMOKE_TEST_OK");
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error("SMOKE_TEST_FAILED", e);
  process.exit(1);
});

