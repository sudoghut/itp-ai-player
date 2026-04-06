# fishframe.net/itp automation starter

This workspace contains minimal automation starters for opening and inspecting `https://fishframe.net/itp` from VS Code.

## Recommended path

Use the Python version in this repo because the current machine has Python available but Node is not activated correctly through `nvm`.

## Python setup

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```powershell
python scripts/open_game.py
```

This opens the page and saves a screenshot to `artifacts/game-home.png`.

## Inspect mode

```powershell
python scripts/inspect_game.py
```

This runs headless, captures a screenshot, and writes a basic DOM summary to `artifacts/page-summary.json`.

## Probe the game flow

```powershell
python scripts/probe_game_flow.py
```

This clicks through the main game entry links and writes per-step summaries to `artifacts/game-flow.json`.

## Run the autonomous test session

```powershell
python scripts/run_test_session.py
```

This performs a repeatable smoke and exploratory pass on the landing page and the canvas game, then writes results to `artifacts/test-session/report.json`.

## Inspect runtime

```powershell
python scripts/inspect_runtime.py
```

This inspects the game page runtime, script bundle markers, and canvas state after load.

## Long load probe

```powershell
python scripts/long_load_probe.py
```

This observes the desktop game loading sequence for about 3 minutes and stores periodic screenshots.

## Guest flow probe

```powershell
python scripts/guest_flow_probe.py
```

This waits for the desktop main menu, enters via guest login, and captures follow-up gameplay screens.

## Node setup

Node files are also included, but they require a working local Node installation first:

```powershell
npm install
npx playwright install chromium
```
