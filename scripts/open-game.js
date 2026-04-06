const { chromium } = require("playwright");

const GAME_URL = process.env.GAME_URL || "https://fishframe.net/itp";
const HEADLESS = process.env.HEADLESS === "1";

async function main() {
  const browser = await chromium.launch({
    headless: HEADLESS,
    slowMo: HEADLESS ? 0 : 150,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  page.on("console", (msg) => {
    console.log(`[browser:${msg.type()}] ${msg.text()}`);
  });

  await page.goto(GAME_URL, {
    waitUntil: "domcontentloaded",
    timeout: 60_000,
  });

  console.log(`Opened: ${page.url()}`);
  console.log(`Title: ${await page.title()}`);

  await page.waitForTimeout(5_000);
  await page.screenshot({
    path: "artifacts/game-home.png",
    fullPage: true,
  });

  if (HEADLESS) {
    await browser.close();
    return;
  }

  console.log("Browser left open for manual inspection. Press Ctrl+C in the terminal to stop.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
