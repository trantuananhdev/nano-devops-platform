const { createOpenAiProvider } = require("./openaiProvider");
const { createClaudeProvider } = require("./claudeProvider");
const { createGeminiProvider } = require("./geminiProvider");

function createLlmProvider() {
  const provider = String(process.env.LLM_PROVIDER || "openai").toLowerCase().trim();

  if (provider === "openai") {
    return createOpenAiProvider();
  }

  if (provider === "anthropic" || provider === "claude") {
    return createClaudeProvider();
  }

  if (provider === "google" || provider === "gemini") {
    return createGeminiProvider();
  }

  throw new Error(`LLM provider '${provider}' not supported. Supported: openai, anthropic, google.`);
}

module.exports = { createLlmProvider };

