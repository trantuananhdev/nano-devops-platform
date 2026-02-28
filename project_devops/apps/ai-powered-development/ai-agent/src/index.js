const { startServerAndWorker } = require("./system/start");

startServerAndWorker()
  .then(() => {
    // eslint-disable-next-line no-console
    console.log("[dfte] boot complete");
  })
  .catch((err) => {
    // eslint-disable-next-line no-console
    console.error("[dfte] boot failed", err);
    process.exit(1);
  });

