import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright


GAME_URL = "https://play.fishframe.net/itp/"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROOT = Path("artifacts") / "interactive-session"
USER_DATA_DIR = ROOT / "user-data"
COMMANDS_FILE = ROOT / "commands.jsonl"
STATUS_FILE = ROOT / "status.json"
SCREENSHOT_FILE = ROOT / "latest.png"
SEEN_FILE = ROOT / "seen_ids.json"
NETWORK_LOG = ROOT / "network-log.jsonl"


def load_seen_ids() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))


def save_seen_ids(seen: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=True, indent=2), encoding="utf-8")


def append_network_log(entry: dict) -> None:
    with open(NETWORK_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def write_status(page, state: str, extra: dict[str, Any] | None = None) -> None:
    canvas = await page.evaluate(
        """
        () => {
          const canvas = document.querySelector("canvas");
          return canvas ? {
            width: canvas.width,
            height: canvas.height,
            clientWidth: canvas.clientWidth,
            clientHeight: canvas.clientHeight
          } : null;
        }
        """
    )
    status = {
        "state": state,
        "url": page.url,
        "title": await page.title(),
        "canvas": canvas,
    }
    if extra:
        status.update(extra)
    STATUS_FILE.write_text(json.dumps(status, ensure_ascii=True, indent=2), encoding="utf-8")
    await page.screenshot(path=str(SCREENSHOT_FILE), full_page=True)


async def ensure_page(context):
    page = context.pages[0] if context.pages else await context.new_page()
    if page.url in ("about:blank", "chrome://new-tab-page/"):
        await page.goto(GAME_URL, wait_until="domcontentloaded", timeout=60_000)
    return page


async def execute_command(page, command: dict[str, Any]) -> dict | None:
    kind = command.get("command")
    if kind == "click":
        x, y = command["x"], command["y"]
        await page.mouse.click(x, y)
    elif kind == "move":
        x, y = command["x"], command["y"]
        await page.mouse.move(x, y)
    elif kind == "hover":
        x, y = command["x"], command["y"]
        await page.mouse.move(x, y)
        await page.wait_for_timeout(command.get("ms", 1000))
    elif kind == "press":
        await page.keyboard.press(command["key"])
    elif kind == "type":
        await page.keyboard.type(command["text"], delay=command.get("delay", 80))
    elif kind == "wait":
        await page.wait_for_timeout(command.get("ms", 1000))
    elif kind == "goto":
        await page.goto(command.get("url", GAME_URL), wait_until="domcontentloaded", timeout=60_000)
    elif kind == "screenshot":
        path = ROOT / command.get("name", "manual.png")
        await page.screenshot(path=str(path), full_page=True)
    elif kind == "eval":
        result = await page.evaluate(command["js"])
        # Write eval result to a file
        eval_result_file = ROOT / "eval-result.json"
        eval_result_file.write_text(
            json.dumps({"id": command.get("id"), "result": result}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"eval_result": result}
    elif kind == "spiral_hover":
        # Spiral hover around (cx, cy) with given radius, taking screenshots
        # when the page title changes (indicating a tooltip appeared).
        # Usage: {"command": "spiral_hover", "x": 384, "y": 681, "radius": 20, "name": "card1.png"}
        import math
        cx, cy = command["x"], command["y"]
        radius = command.get("radius", 20)
        step_delay = command.get("step_ms", 150)
        name = command.get("name", "spiral.png")
        old_title = await page.title()
        found = False

        # Generate spiral points: center, then rings at r=10 and r=radius
        points = [(cx, cy)]
        for r in [10, radius]:
            for i in range(8):
                angle = 2 * math.pi * i / 8
                points.append((int(cx + r * math.cos(angle)), int(cy + r * math.sin(angle))))

        for px, py in points:
            await page.mouse.move(px, py)
            await page.wait_for_timeout(step_delay)
            new_title = await page.title()
            if new_title != old_title:
                # Title changed — tooltip likely appeared, screenshot immediately
                path = ROOT / name
                await page.screenshot(path=str(path), full_page=True)
                found = True
                break

        if not found:
            # No tooltip detected, screenshot anyway for debugging
            path = ROOT / name
            await page.screenshot(path=str(path), full_page=True)

    elif kind == "stop":
        raise SystemExit(0)
    return None


def setup_network_logging(page) -> None:
    """Attach request/response listeners to capture all network traffic."""

    async def on_request(request):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "method": request.method,
            "url": request.url,
            "resource_type": request.resource_type,
            "post_data": None,
        }
        # Capture POST body for API calls
        if request.method == "POST" and request.post_data:
            try:
                entry["post_data"] = json.loads(request.post_data)
            except (json.JSONDecodeError, TypeError):
                entry["post_data"] = request.post_data[:2000] if request.post_data else None
        # Only log XHR/fetch/websocket, skip images/scripts/stylesheets
        if request.resource_type in ("xhr", "fetch", "websocket", "other"):
            append_network_log(entry)

    async def on_response(response):
        request = response.request
        if request.resource_type not in ("xhr", "fetch", "websocket", "other"):
            return
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "method": request.method,
            "url": response.url,
            "status": response.status,
            "body": None,
        }
        try:
            body = await response.text()
            # Try to parse as JSON
            try:
                entry["body"] = json.loads(body)
            except (json.JSONDecodeError, TypeError):
                entry["body"] = body[:5000] if body else None
        except Exception:
            entry["body"] = "<failed to read>"
        append_network_log(entry)

    page.on("request", on_request)
    page.on("response", on_response)


async def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    COMMANDS_FILE.touch(exist_ok=True)

    # Clear old network log
    if NETWORK_LOG.exists():
        NETWORK_LOG.unlink()

    seen = load_seen_ids()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            executable_path=CHROME_PATH,
            headless=False,
            args=[
                "--no-proxy-server",
                "--proxy-server=direct://",
                "--proxy-bypass-list=*",
            ],
            viewport={"width": 1440, "height": 900},
        )
        page = await ensure_page(context)

        # Attach network logging
        setup_network_logging(page)

        await write_status(page, "ready", {"message": "interactive session started with network logging"})

        while True:
            page = await ensure_page(context)
            lines = [line for line in COMMANDS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
            new_commands = []
            for line in lines:
                payload = json.loads(line)
                command_id = str(payload["id"])
                if command_id not in seen:
                    new_commands.append(payload)

            for payload in new_commands:
                seen.add(str(payload["id"]))
                await write_status(page, "executing", {"currentCommand": payload})
                await execute_command(page, payload)
                save_seen_ids(seen)
                await write_status(page, "ready", {"lastCommand": payload})

            save_seen_ids(seen)
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
