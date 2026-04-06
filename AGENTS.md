# Agent Notes

## Project purpose

This workspace is for automated testing of the web game at `https://fishframe.net/itp` and `https://play.fishframe.net/itp/`.

## Verified game stack

- The playable page is a `Godot + WebAssembly + WebGL2` canvas application.
- The marketing/landing page is standard DOM.
- The game page can take a long time to load before the real menu appears.

## Login and progression notes

- Credentials are stored in `.env` file (see `.env.sample` for format):
  - Username: `$GAME_USERNAME`
  - Password: `$GAME_PASSWORD`
- Intended login flow from the user:
  - Click `入卷`
  - Click `生存模式` page's `开始游戏`
  - After loading completes, press `Space` to advance

## Important observed behavior

- The game does not always reach the menu quickly.
- A long loading screen is normal on first entry and may last more than 60 seconds.
- `artifacts/stage-start-game.png` is still part of the loading stage, not the login page.
- After that loading page appears, agents should wait longer before attempting login interactions.
- For this game, repeated relaunch/reload is a bad testing strategy because one load can take many minutes.
- Prefer a single persistent browser session and continue all clicks/keys inside that same live session.
- After loading, there can be a black intro scene before the menu.
- The black intro scene shows text equivalent to:
  - Hold to accelerate
  - Click the upper-right corner to skip
- Reaching a full-size `1440x900` canvas does not always mean the menu is ready; sometimes the black intro scene is still active.

## Menu interaction pitfalls

- `游客登录` has not yet been triggered reliably by automation.
- Simple coordinate clicking on the visible `游客登录` button was not sufficient in repeated tests.
- Keyboard navigation is partially active:
  - `Tab` + `Enter` can trigger menu actions.
  - One confirmed result is the validation message `请先填写署名与密码`, which indicates regular login was triggered without valid input.
- The login UI appears to be drawn inside canvas or canvas-managed layers, so DOM selectors are not available for the visible menu controls.
- On the real login page:
  - Username field can be filled by click + type.
  - Password entry is more reliable via `Tab` from the username field, then type the password.
  - This was verified in the persistent live session.
- After successful `入卷`, the game reaches a mode selection page with:
  - `生存模式`
  - `自由模式`
- On that mode selection page, the left `生存模式` card can reveal a `开始游戏` button.
- At that stage, the correct action is simple: click `开始游戏`.
- Do not inject extra exploratory inputs at that stage unless the single click clearly fails.

## Stability issues

- Earlier tests showed `ERR_CONNECTION_CLOSED` on both:
  - `https://fishframe.net/itp`
  - `https://play.fishframe.net/itp/`
- This should no longer be treated as a confirmed site-wide outage.
- Updated finding:
  - Playwright's bundled Chromium path produced repeated `ERR_CONNECTION_CLOSED`.
  - Switching to the system Chrome executable restored connectivity.
  - The problem appears environment-specific to the automation browser path, not a universal site availability issue.

## Browser selection rule

- Prefer the system Chrome executable for this site:
  - `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Keep direct-connection launch arguments:
  - `--no-proxy-server`
  - `--proxy-server=direct://`
  - `--proxy-bypass-list=*`
- Do not default to Playwright's bundled Chromium for this game unless system Chrome is unavailable.

## Connection rule

- Do not use any proxy to connect to the site.
- Future agents should use direct connections only.

## Entry URL rule

- Treat `https://play.fishframe.net/itp/` as the primary game login page.
- `https://fishframe.net/itp` is the landing/marketing page that links into the actual game.
- For gameplay automation and authenticated testing, prefer opening `https://play.fishframe.net/itp/` directly.

## Evidence locations

- Runtime inspection: `artifacts/runtime-inspect.json`
- Smoke/exploratory test session: `artifacts/test-session/report.json`
- Long load probe: `artifacts/long-load-probe/report.json`
- Guest flow probe: `artifacts/guest-flow-probe/report.json`
- Keyboard menu probe: `artifacts/guest-keyboard-search/report.json`
- Authenticated flow attempt: `artifacts/authenticated-flow/report.json`

## Choice card interaction (verified)

- During story mode, choices appear as wooden card tags at the bottom of the canvas.
- Each card has a single Chinese character written on it (e.g. `入`, `出`, `戒`).
- **Hover**: move the mouse onto the **character text** on the card to reveal a tooltip with the choice title and description. Hovering between cards or on the card edges does NOT trigger the tooltip.
- **Verified card text positions** (in 1440×900 canvas):
  - Left card text: approximately `x=350, y=730`
  - Middle card text: approximately `x=670, y=770` (noticeably lower and slightly right of center compared to the other two cards; verified via matrix scan on 2026-04-06)
  - Right card text: approximately `x=1030, y=730`
- **Four-card layout** (when 4 choices appear) — verified via `document.addEventListener('mousemove')` coordinate capture:
  - Card 1 text: approximately `x=384, y=642` (verified via mousemove listener 2026-04-06)
  - Card 2 text: approximately `x=608, y=703` (verified via mousemove listener 2026-04-06)
  - Card 3 text: approximately `x=810, y=730`
  - Card 4 text: approximately `x=1080, y=730`
- **IMPORTANT**: Card hover positions are `clientX/clientY` coordinates (viewport-relative). Visual estimation from screenshots is unreliable (can be off by 90+ px). When in doubt, use `document.addEventListener('mousemove', e => document.title = e.clientX + ',' + e.clientY)` to capture exact coordinates.
- Card positions vary between layouts and choice events. If hover fails, try coordinates ±30px in both x and y.
- **Selecting a choice**: click the card text to open the choice preview popup, then click the `确认选择` (confirm) button at approximately `x=720, y=548`. `Tab` + `Enter` does NOT reliably confirm choices — always click the button directly.
- **"好的" button**: Achievement popups may appear with a `好的` (OK) button. Click at approximately `x=720, y=590` to dismiss.
- The interactive session runner supports `hover` and `move` commands (added 2026-04-06) for this purpose.

## Gameplay operation rules

- **Screenshot first**: Always screenshot and evaluate the current state before performing any action.
- **Space only for dialogue**: Only use Space to advance dialogue text. Never mix in clicks during dialogue advancement.
- **Choice handling**: When choice cards appear, STOP. Hover **every** card and confirm you have read its tooltip before proceeding. **Do NOT select any card until all options have been successfully evaluated.** If a hover fails to show a tooltip, retry with adjusted coordinates — never skip a card. After all cards are read, **read `artifacts/game-history.json`** to review past playthroughs, choices, outcomes, and lessons learned before making a decision. Analyze all information, then deliberately click the chosen card and confirm.
- **Confirm button**: After clicking a choice card, click `确认选择` at approximately `x=720, y=548`. Do NOT use Tab+Enter.
- **"好的" button**: Achievement/reward popups need the `好的` button clicked at approximately `x=724, y=505` (verified via mousemove listener 2026-04-06).
- **"继续" button**: On ending screens, the `继续` (continue) button is at approximately `x=436, y=764` (verified via mousemove listener 2026-04-06).
- **Follow in-game prompts**: If the game text mentions `落笔` (bottom-right button) or other UI elements, follow those prompts instead of blindly pressing Space. The `落笔` button is at approximately bottom-right corner of the screen.
- **Risk assessment before every choice**: Before selecting any option, explicitly evaluate each choice's risk level (low/medium/high/fatal). Consider: (1) Has a similar risky action caused death in past playthroughs? (e.g., theft→庞组儿死, confronting powerful enemies→吴小六死, dangerous missions→杨怀瑾死) (2) Does this choice put the character in physical danger or legal jeopardy? (3) Does the reward justify the risk given current resource levels? Prefer medium-risk choices that build connections over high-risk gambles or zero-risk passive options.
- **Balance resources**: Pay close attention to all four stats (资财/势望/人情/心性). Avoid letting any single resource become critically depleted — when 资财 reaches zero, the character deteriorates rapidly (郭振声's lesson). When making choices, consider whether a resource is dangerously low and prioritize recovery.
- **Read all narrative text**: Carefully read every line of story/dialogue text in screenshots — not just choice descriptions. Use the narrative context (character actions, setting details, NPC behavior, foreshadowing) to inform strategic decisions.
- **No batch commands**: Send one action at a time, screenshot after each, evaluate before next action.

## Game history and memory

- Full playthrough records: `artifacts/game-history.json`
- Contains: character, choices, outcomes, endings, lessons learned for each playthrough
- **How to use**: Before making any choice, read `game-history.json` and check:
  1. Has a similar choice appeared in past playthroughs? What was the outcome?
  2. What lessons were learned from previous endings?
  3. What strategy is the current playthrough following?
- **After each choice**: Update `game-history.json` with the choice made and its result
- **After each ending**: Record the full ending, stats, and new lessons learned
- **Key learnings so far**:
  - Passive/conservative choices lead to poverty and death
  - Active community-building choices create connections needed for 群像结局
  - Must keep companions alive AND connected through the Jingkang Incident (1127)
  - Resource management matters: don't let wealth reach zero

## Recommended next steps for future agents

- If connectivity fails in automation, switch to system Chrome first before concluding the site is down.
- Prefer direct access to `https://play.fishframe.net/itp/` for gameplay automation.
- Wait up to 2-3 minutes before concluding the menu failed to load.
- Treat the black intro scene and the main menu as separate states.
- Use a persistent session runner for story/gameplay testing. Do not restart the game between adjacent test steps unless the session is unrecoverable.
- For authenticated testing, try a more systematic canvas interaction strategy:
  - OCR-assisted button detection
  - Pixel-based state detection
  - Broader keyboard focus traversal
  - Coordinate search around `入卷`, `游客登录`, and `开始游戏`
