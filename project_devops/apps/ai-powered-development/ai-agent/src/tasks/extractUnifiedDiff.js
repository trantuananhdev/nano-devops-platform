/**
 * extractUnifiedDiff.js
 *
 * Vấn đề gốc: LLM đôi khi chèn text giải thích VÀO TRONG khối diff,
 * hoặc output nhiều code block, hoặc không dùng header chuẩn.
 *
 * Giải pháp:
 * 1. Tìm và extract khối ```diff ... ``` hoặc ``` ... ```
 * 2. Clean patch: bỏ dòng không phải diff, normalize line endings
 * 3. Validate: phải có ít nhất 1 hunk header @@
 * 4. Fallback: tìm raw "diff --git" trong text
 */

const HUNK_HEADER_RE = /^@@\s+-\d+/m;
const DIFF_LINE_RE   = /^(diff --git |---|[+]{3}|@@|[ +\-\\])/;
const NO_NEWLINE_RE  = /^\\ No newline at end of file/i;

/**
 * Normalize line endings về LF, bỏ trailing spaces.
 */
function normalizeLineEndings(text) {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n");
}

/**
 * Clean một patch block thô:
 * - Bỏ các dòng không phải diff syntax ở đầu/cuối
 * - Normalize CRLF → LF
 * - Bỏ BOM nếu có
 */
function cleanPatchBlock(raw) {
  const text = normalizeLineEndings(raw)
    .replace(/^\uFEFF/, ""); // BOM

  const lines = text.split("\n");
  const result = [];
  let inDiff = false;

  for (const line of lines) {
    // Bắt đầu từ dòng diff --git hoặc ---
    if (!inDiff) {
      if (line.startsWith("diff --git ") || line.startsWith("--- ")) {
        inDiff = true;
        result.push(line);
      }
      // Bỏ qua text giải thích trước diff
      continue;
    }

    // Trong diff rồi — kiểm tra dòng có hợp lệ không
    if (DIFF_LINE_RE.test(line) || NO_NEWLINE_RE.test(line)) {
      result.push(line);
    } else if (line === "") {
      // Dòng trống trong diff thường là context line bị mất dấu cách
      result.push(" " + line);
    } else {
      // Dòng lạ: có thể là context line bị mất dấu cách ở đầu
      // Nếu nó không phải là header mới, ta thử cứu bằng cách thêm dấu cách
      if (!line.startsWith("diff --git") && !line.startsWith("--- ") && !line.startsWith("+++ ")) {
        result.push(" " + line);
      } else {
        if (result.length > 3) break;
      }
    }
  }

  const cleaned = result.join("\n").trimEnd();

  // Validate: phải có hunk header @@
  if (!HUNK_HEADER_RE.test(cleaned)) return null;

  return cleaned;
}

/**
 * Main export: extract và clean unified diff từ LLM output.
 */
function extractUnifiedDiff(text) {
  if (!text) return null;

  const str = String(text);

  // ── Strategy 1: fenced ```diff ... ``` block ──────────────────────────
  // Lấy TẤT CẢ code block, thử từng cái
  const fenceRe = /```(?:diff|patch)?\s*\n([\s\S]*?)```/gi;
  let match;
  while ((match = fenceRe.exec(str)) !== null) {
    const candidate = cleanPatchBlock(match[1]);
    if (candidate) return candidate;
  }

  // ── Strategy 2: raw diff --git trong text ────────────────────────────
  const gitIdx = str.indexOf("diff --git ");
  if (gitIdx >= 0) {
    const candidate = cleanPatchBlock(str.slice(gitIdx));
    if (candidate) return candidate;
  }

  // ── Strategy 3: raw --- a/ ... +++ b/ trong text ─────────────────────
  const minusIdx = str.indexOf("--- a/");
  if (minusIdx >= 0) {
    const candidate = cleanPatchBlock(str.slice(minusIdx));
    if (candidate) return candidate;
  }

  return null;
}

module.exports = { extractUnifiedDiff };