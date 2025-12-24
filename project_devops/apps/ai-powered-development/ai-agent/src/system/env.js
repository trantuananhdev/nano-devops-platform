const dotenv = require("dotenv");
const fs = require("fs");

/**
 * Load secrets from files if _FILE suffix is used (Docker Secrets support)
 */
function loadSecretFiles() {
  const fileSuffix = "_FILE";
  Object.keys(process.env).forEach((key) => {
    if (key.endsWith(fileSuffix)) {
      const realKey = key.slice(0, -fileSuffix.length);
      const filePath = process.env[key];
      if (fs.existsSync(filePath)) {
        try {
          process.env[realKey] = fs.readFileSync(filePath, "utf8").trim();
        } catch (err) {
          // eslint-disable-next-line no-console
          console.error(`[dfte] Error reading secret from ${filePath}:`, err.message);
        }
      }
    }
  });
}

function loadEnv() {
  dotenv.config();
  
  // Senior Fix: Load secrets from files BUT priority is given to direct ENV variables
  // This ensures that when the user updates .env, it takes effect immediately
  loadSecretFiles();

  const required = [
    "DATABASE_URL",
    "JWT_SECRET",
    "ADMIN_API_KEY",
    "LLM_PROVIDER",
  ];

  const optional = [
    "GITHUB_WEBHOOK_SECRET",
    "GITHUB_TOKEN",
    "GITLAB_TOKEN",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_MODEL",
    "GIT_USER_NAME",
    "GIT_USER_EMAIL",
    "BOOTSTRAP_REPO_FULL_NAME",
    "BOOTSTRAP_GITHUB_TOKEN",
  ];

  const missing = required.filter((k) => !process.env[k] || !String(process.env[k]).trim());
  
  // Conditional check for LLM Keys
  const provider = process.env.LLM_PROVIDER || "gemini";
  if (provider === "gemini" && !process.env.GEMINI_API_KEY) {
    missing.push("GEMINI_API_KEY");
  } else if (provider === "openai" && !process.env.OPENAI_API_KEY) {
    missing.push("OPENAI_API_KEY");
  }

  if (missing.length) {
    const errorMsg = `[FATAL] Missing required environment variables: ${missing.join(", ")}`;
    // eslint-disable-next-line no-console
    console.error(errorMsg);
    // In production, we must fail immediately if secrets are missing
    if (process.env.NODE_ENV === "production") {
      throw new Error(errorMsg);
    }
  }

  // Log availability of optional keys (without showing values)
  optional.forEach(k => {
    if (process.env[k]) {
      // eslint-disable-next-line no-console
      console.log(`[dfte] ${k} is configured`);
    }
  });
}

module.exports = { loadEnv };

