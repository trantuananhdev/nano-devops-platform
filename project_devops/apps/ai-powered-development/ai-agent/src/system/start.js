const http = require("http");
const { loadEnv } = require("./env");
const { initDb } = require("../adapters/db/initDb");
const { createApiApp } = require("./apiApp");
const { startTaskWorker } = require("./taskWorker");

async function startServerAndWorker() {
  loadEnv();

  // Retry database initialization (useful for fresh platform boot)
  let retries = 5;
  while (retries > 0) {
    try {
      await initDb();
      break;
    } catch (err) {
      retries -= 1;
      // eslint-disable-next-line no-console
      console.error(`[dfte] Database initialization failed. Retrying... (${retries} retries left)`, err.message);
      if (retries === 0) throw err;
      await new Promise(r => setTimeout(r, 5000));
    }
  }

  const app = createApiApp();
  const server = http.createServer(app);

  const port = process.env.PORT ? Number(process.env.PORT) : 3000;

  server.listen(port, () => {
    // eslint-disable-next-line no-console
    console.log(`[dfte] API listening on http://localhost:${port}`);
  });

  // Background worker (in same process) to keep MVP simple.
  startTaskWorker();
}

module.exports = { startServerAndWorker };

