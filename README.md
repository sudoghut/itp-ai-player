# Into the Painting (入画) - AI Player

Automated game testing project for [Into the Painting](https://play.fishframe.net/itp/), a Godot WebAssembly narrative game set in Northern Song Dynasty China.

## About the Game

[**Into the Painting**](https://fishframe.net/itp) (入画) is an AI-driven open narrative game based on the classical painting *Along the River During the Qingming Festival* (清明上河图). Players step into the historical city of Bianjing (汴京), inhabiting characters from different social classes — exploring their birth, occupation, relationships, and private longings while making choices that ripple through an interconnected social network. Each playthrough generates a unique storyline with multiple possible endings powered by real-time AI simulation.

The game is built on the **FISH** (Framework for Interactive Simulation of History) framework at the University of Hong Kong's Faculty of Arts, supported by the Arts Tech Lab. It is currently in a non-commercial playtest phase focused on AI-driven interactive historical simulation and digital humanities research.

## Acknowledgments

This automation project is built to interact with *Into the Painting*, and we sincerely thank its creators for this inspiring work:

- **Yuqi Chen** (陈钰琪), Assistant Professor, University of Hong Kong — Producer, prototype design, system design, development, and narrative design
- **Yulou Qingge** (雨楼清歌) — Co-producer, interaction design, narrative design, and animation editing

Thank you for bringing the world inside the scroll to life.

---

## How It Works

This project uses an AI agent (Claude) + Playwright to play the game autonomously via a persistent Chrome browser session. The agent reads screenshots, analyzes choices, and makes strategic decisions based on accumulated playthrough history.

## Getting Started

### Prerequisites

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Credentials

Copy `.env.sample` to `.env` and fill in your game credentials:

```
GAME_USERNAME=your_username
GAME_PASSWORD=your_password
```

### Recommended Usage

1. **Start the interactive session runner**, which opens a persistent Chrome browser:

   ```powershell
   python scripts/interactive_session_runner.py
   ```

2. **Complete login and enter the game manually.** The runner opens a visible browser window. Log in with your account, select a character, and advance until you reach the gameplay screen (where you see the character's stats panel and narrative text / choice cards).

3. **Hand off to the AI agent.** Once you are on the gameplay screen, let the agent take over. Tell your agent something like:

   > Play this game following the rules in AGENTS.md. Don't ask me for confirmation — keep playing autonomously, make optimal choices, and record every decision to artifacts/game-history.json.

   The agent will:
   - Read choice cards by hovering over them
   - Analyze options against past playthrough lessons (`artifacts/game-history.json`)
   - Make strategic decisions following the rules in `AGENTS.md`
   - Advance dialogue and handle UI interactions automatically
   - Record all choices, outcomes, and lessons learned

### Why Manual Login?

The game site uses authentication that is difficult to automate reliably. Having the user complete login ensures the session is properly established before automation begins. This also avoids storing credentials in automation scripts.

## Key Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Rules, coordinates, strategies, and game knowledge for the AI agent |
| `artifacts/game-history.json` | All playthrough records with choices, outcomes, and lessons |
| `scripts/interactive_session_runner.py` | Core automation runner - polls `commands.jsonl` and executes actions |
| `scripts/send_cmds.py` | Helper to append commands to the queue |
| `.env` | Game credentials (not committed) |

## Architecture

```
User (login) --> Chrome browser <-- interactive_session_runner.py
                                         ^
                                         |
                                    commands.jsonl <-- AI Agent (Claude)
                                         |
                                         v
                                    screenshots --> AI Agent reads & decides
```

The runner watches `artifacts/interactive-session/commands.jsonl` for new commands (click, hover, screenshot, press, etc.) and executes them against the browser. The AI agent writes commands to this file and reads back screenshots to understand the game state.
