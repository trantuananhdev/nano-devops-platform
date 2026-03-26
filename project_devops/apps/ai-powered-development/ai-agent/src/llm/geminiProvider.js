const axios = require("axios");

function createGeminiProvider() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error("GEMINI_API_KEY is not set");

  // Always use gemini-2.5-flash as per user's preference
  const model = "gemini-2.5-flash";
  const apiVersion = "v1beta";
  const temperature = 0.2;
  const maxTokens = 2048;

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
      ]
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

    const text = resp.data?.candidates?.[0]?.content?.parts?.[0]?.text || "No response";

    if (text === "No response") {
      throw new Error(`Gemini returned empty or invalid response: ${JSON.stringify(resp.data)}`);
    }

    // Clean markdown if present
    let cleanedText = text.trim();
    if (cleanedText.startsWith("```")) {
      const lines = cleanedText.split("\n");
      if (lines.length >= 2) {
        const startIdx = lines[0].startsWith("```") ? 1 : 0;
        const lastIdx = lines.length - 1;
        const endIdx = lines[lastIdx].trim() === "```" ? lastIdx : undefined;
        cleanedText = lines.slice(startIdx, endIdx).join("\n").trim();
      }
    }

    return cleanedText;
  }

  return { chatText, model, temperature, maxTokens };
}

module.exports = { createGeminiProvider };
