# Into the Painting — AI Player

## About the Game

[**Into the Painting**](https://fishframe.net/itp) (入画) is an AI-driven open narrative game based on the classical painting *Along the River During the Qingming Festival* (清明上河图). Players step into the historical city of Bianjing (汴京), inhabiting characters from different social classes — exploring their birth, occupation, relationships, and private longings while making choices that ripple through an interconnected social network. Each playthrough generates a unique storyline with multiple possible endings powered by real-time AI simulation.

The game is built on the **FISH** (Framework for Interactive Simulation of History) framework at the University of Hong Kong's Faculty of Arts, supported by the Arts Tech Lab. It is currently in a non-commercial playtest phase focused on AI-driven interactive historical simulation and digital humanities research.

## Acknowledgments

This automation project is built to interact with *Into the Painting*, and we sincerely thank its creators for this inspiring work:

- **Yuqi Chen** (陈钰琪), Assistant Professor, University of Hong Kong — Producer, prototype design, system design, development, and narrative design
- **Yulou Qingge** (雨楼清歌) — Co-producer, interaction design, narrative design, and animation editing

Thank you for bringing the world inside the scroll to life.

---

## What This Repo Does

This workspace contains automation scripts for opening, inspecting, and playing [fishframe.net/itp](https://fishframe.net/itp) programmatically.

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
