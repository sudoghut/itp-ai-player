# Agent Notes

## Project purpose

This workspace is for automated gameplay of the web game at `https://play.fishframe.net/itp/`.

## Game stack

- Godot + WebAssembly + WebGL2 canvas application.
- The game page can take a long time to load (60+ seconds on first entry).
- Login is handled manually by the user before the agent takes over.

## Browser setup

- Use the system Chrome executable: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Launch with direct-connection arguments: `--no-proxy-server`, `--proxy-server=direct://`, `--proxy-bypass-list=*`
- Do not use Playwright's bundled Chromium for this game.
- Use a single persistent browser session. Do not restart the game between steps.

## Screenshot-first rule

Always screenshot and read the image before performing any action. Evaluate the current game state from the screenshot, then decide the next step. This applies to all phases — dialogue, transitions, choices, and any other interaction.

## Sending commands to the runner

- Use `scripts/send_cmds.py` to append commands to the queue. Do NOT create new scripts for sending commands — this helper already exists.
- Alternatively, write commands inline with `python -c "import json; ..."` appending to `artifacts/interactive-session/commands.jsonl`.
- Available commands: `click`, `hover`, `press`, `wait`, `screenshot`, `eval`, `move`, `type`, `goto`, `stop`.

## Skills (auto-loaded when relevant)

- **`interact`** — Card interaction coordinates and UI button positions (`.claude/skills/interact.md`)
- **`make-choice`** — Decision-making workflow when choice cards appear (`.claude/skills/make-choice.md`)
