const axios = require("axios");

function createGeminiProvider() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error("GEMINI_API_KEY is not set");

  // Default to gemini-2.5-flash as per user's preference
  const model = process.env.GEMINI_MODEL || "gemini-2.5-flash";
  const apiVersion = process.env.GEMINI_API_VERSION || "v1beta";
  const temperature = process.env.GEMINI_TEMPERATURE ? Number(process.env.GEMINI_TEMPERATURE) : 0.2;
  const maxTokens = process.env.GEMINI_MAX_TOKENS ? Number(process.env.GEMINI_MAX_TOKENS) : 2048;

  async function chatText({ messages }) {
    // Senior Fix: Align with user provided sample business logic
    // User sample uses a simple: { contents: [{ parts: [{ text: prompt }] }] }
    
    const systemMessage = messages.find((m) => m.role === "system");
    const userMessages = messages.filter((m) => m.role !== "system");

    // Merge system instruction and user prompt into a single text block
    let prompt = "";
    if (systemMessage) {
      prompt += `[INSTRUCTION]\n${systemMessage.content}\n\n`;
    }
    prompt += userMessages.map(m => m.content).join("\n\n");

    const body = {
      contents: [
        {
          parts: [{ text: prompt }]
        }
      ],
      generationConfig: {
        temperature,
        maxOutputTokens: maxTokens,
      },
    };

    const url = `https://generativelanguage.googleapis.com/${apiVersion}/models/${model}:generateContent?key=${apiKey}`;
    
    const resp = await axios.post(
      url,
      body,
      {
        headers: {
          "Content-Type": "application/json",
        },
        timeout: Number(process.env.GEMINI_TIMEOUT_MS || 60000),
      }
    );

    const text =
      resp.data &&
      resp.data.candidates &&
      resp.data.candidates[0] &&
      resp.data.candidates[0].content &&
      resp.data.candidates[0].content.parts &&
      resp.data.candidates[0].content.parts[0] &&
      resp.data.candidates[0].content.parts[0].text;

    if (!text) {
      throw new Error(`Gemini returned empty or invalid response: ${JSON.stringify(resp.data)}`);
    }

    return text;
  }

  return { chatText, model, temperature, maxTokens };
}

module.exports = { createGeminiProvider };
