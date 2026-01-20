const axios = require("axios");

function createClaudeProvider() {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY is not set");

  const model = process.env.ANTHROPIC_MODEL || "claude-3-5-sonnet-20240620";
  const maxTokens = process.env.ANTHROPIC_MAX_TOKENS ? Number(process.env.ANTHROPIC_MAX_TOKENS) : 4096;

  async function chatText({ messages }) {
    // Convert OpenAI messages format to Anthropic format if needed
    // Anthropic uses system as a top-level param, not in messages array for some versions
    const systemMessage = messages.find(m => m.role === 'system');
    const userMessages = messages.filter(m => m.role !== 'system');

    const resp = await axios.post(
      "https://api.anthropic.com/v1/messages",
      {
        model,
        max_tokens: maxTokens,
        system: systemMessage ? systemMessage.content : undefined,
        messages: userMessages.map(m => ({ role: m.role, content: m.content })),
      },
      {
        headers: {
          "x-api-key": apiKey,
          "anthropic-version": "2023-06-01",
          "Content-Type": "application/json",
        },
        timeout: Number(process.env.ANTHROPIC_TIMEOUT_MS || 60000),
      }
    );

    const text = resp.data && resp.data.content && resp.data.content[0] && resp.data.content[0].text;
    if (!text) throw new Error("Anthropic returned empty content");
    return text;
  }

  return { chatText, model, maxTokens };
}

module.exports = { createClaudeProvider };
