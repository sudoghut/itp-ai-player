---
name: make-choice
description: Decision-making workflow when choice cards appear in the ITP game
trigger: when choice cards appear and a gameplay decision needs to be made
---

# Choice Decision Workflow

## Core rules

- **Screenshot first**: Always screenshot and evaluate the current state before performing any action.
- **Space only for dialogue**: Only use Space to advance dialogue text. Never mix in clicks during dialogue advancement.
- **No batch commands**: Send one action at a time, screenshot after each, evaluate before next action.
- **Read all narrative text**: Carefully read every line of story/dialogue text in screenshots — not just choice descriptions. Use the narrative context (character actions, setting details, NPC behavior, foreshadowing) to inform strategic decisions.

## When choice cards appear

1. **STOP.** Hover **every** card and confirm you have read its tooltip before proceeding. Do NOT select any card until all options have been successfully evaluated. If a hover fails to show a tooltip, retry with adjusted coordinates — never skip a card.
2. **Read game history.** After all cards are read, read `artifacts/game-history.json` to review past playthroughs, choices, outcomes, and lessons learned.
   - Has a similar choice appeared in past playthroughs? What was the outcome?
   - What lessons were learned from previous endings?
   - What strategy is the current playthrough following?
3. **Risk assessment.** Before selecting any option, explicitly evaluate each choice's risk level (low/medium/high/fatal). Consider:
   - Has a similar risky action caused death in past playthroughs? (e.g., theft -> 庞组儿死, confronting powerful enemies -> 吴小六死, dangerous missions -> 杨怀瑾死)
   - Does this choice put the character in physical danger or legal jeopardy?
   - Does the reward justify the risk given current resource levels?
   - Prefer medium-risk choices that build connections over high-risk gambles or zero-risk passive options.
4. **Balance resources.** Pay close attention to all four stats (资财/势望/人情/心性). Avoid letting any single resource become critically depleted — when 资财 reaches zero, the character deteriorates rapidly (郭振声's lesson). When making choices, consider whether a resource is dangerously low and prioritize recovery.
5. **Select.** Analyze all information, then deliberately click the chosen card and confirm.
6. **Update history.** After each choice, update `artifacts/game-history.json` with the choice made and its result. After each ending, record the full ending, stats, and new lessons learned.

## Key learnings from past playthroughs

- Passive/conservative choices lead to poverty and death
- Active community-building choices create connections needed for 群像结局
- Must keep companions alive AND connected through the Jingkang Incident (1127)
- Resource management matters: don't let wealth reach zero
