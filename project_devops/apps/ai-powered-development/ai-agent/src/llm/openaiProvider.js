const axios = require("axios");

function createOpenAiProvider() {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("OPENAI_API_KEY is not set");

  const model = process.env.OPENAI_MODEL || "gpt-4.1-mini";
  const temperature = process.env.OPENAI_TEMPERATURE ? Number(process.env.OPENAI_TEMPERATURE) : 0.2;
  const maxTokens = process.env.OPENAI_MAX_TOKENS ? Number(process.env.OPENAI_MAX_TOKENS) : 1500;

  async function chatText({ messages }) {
    const resp = await axios.post(
      "https://api.openai.com/v1/chat/completions",
      {
        model,
        temperature,
        max_tokens: maxTokens,
        messages,
      },
      {
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        timeout: Number(process.env.OPENAI_TIMEOUT_MS || 60000),
      }
    );

    const text = resp.data && resp.data.choices && resp.data.choices[0] && resp.data.choices[0].message && resp.data.choices[0].message.content;
    if (!text) throw new Error("OpenAI returned empty content");
    return text;
  }

  return { chatText, model, temperature, maxTokens };
}

module.exports = { createOpenAiProvider };

