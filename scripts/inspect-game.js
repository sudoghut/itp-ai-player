const fs = require("fs/promises");
const path = require("path");
const { chromium } = require("playwright");

const GAME_URL = process.env.GAME_URL || "https://fishframe.net/itp";

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
  });

  await page.goto(GAME_URL, {
    waitUntil: "domcontentloaded",
    timeout: 60_000,
  });

  await page.waitForTimeout(3_000);

  const summary = await page.evaluate(() => {
    const tags = ["canvas", "iframe", "video", "button", "input"];
    const counts = Object.fromEntries(
      tags.map((tag) => [tag, document.querySelectorAll(tag).length]),
    );

    const buttons = Array.from(document.querySelectorAll("button, a, [role='button']"))
      .slice(0, 20)
      .map((el) => ({
        tag: el.tagName.toLowerCase(),
        text: (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 80),
        id: el.id || null,
        className: el.className || null,
      }));

    return {
      url: location.href,
      title: document.title,
      counts,
      buttons,
    };
  });

  const artifactsDir = path.join(process.cwd(), "artifacts");
  await fs.mkdir(artifactsDir, { recursive: true });
  await fs.writeFile(
    path.join(artifactsDir, "page-summary.json"),
    JSON.stringify(summary, null, 2),
  );

  await page.screenshot({
    path: path.join(artifactsDir, "inspect.png"),
    fullPage: true,
  });

  console.log(JSON.stringify(summary, null, 2));
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
