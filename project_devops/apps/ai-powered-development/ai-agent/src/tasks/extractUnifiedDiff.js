function extractUnifiedDiff(text) {
  if (!text) return null;

  // Prefer fenced diff blocks.
  const fence = String(text).match(/```(?:diff)?\s*([\s\S]*?)```/i);
  if (fence && fence[1]) return fence[1].trim();

  // Fallback: raw git diff starting from "diff --git".
  const idx = String(text).indexOf("diff --git ");
  if (idx >= 0) return String(text).slice(idx).trim();

  return null;
}

module.exports = { extractUnifiedDiff };

