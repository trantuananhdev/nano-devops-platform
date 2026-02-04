const { initDb } = require("./src/adapters/db/initDb");

(async () => {
  try {
    console.log("Initializing Agentic-AI Database...");
    await initDb();
    console.log("Database initialization successful.");
    process.exit(0);
  } catch (err) {
    console.error("Database initialization failed:", err);
    process.exit(1);
  }
})();
