---
name: interact
description: Card interaction coordinates and UI button positions for the ITP game canvas
trigger: when performing hover, click, or UI interactions on the game canvas
---

# Choice Card Interaction

During story mode, choices appear as wooden card tags at the bottom of the canvas. Each card has a single Chinese character written on it (e.g. `入`, `出`, `戒`).

## Hover to reveal tooltip

Move the mouse onto the **character text** on the card to reveal a tooltip with the choice title and description. Hovering between cards or on the card edges does NOT trigger the tooltip.

## Card text positions (1440x900 canvas)

### Three-card layout
- Left card text: approximately `x=350, y=730`
- Middle card text: approximately `x=670, y=770`
- Right card text: approximately `x=1030, y=730`

### Four-card layout
- Card 1: approximately `x=384, y=642`
- Card 2: approximately `x=608, y=703`
- Card 3: approximately `x=810, y=730`
- Card 4: approximately `x=1080, y=730`

## Coordinate troubleshooting

Card hover positions are `clientX/clientY` coordinates. If hover fails, try coordinates +/-30px in both x and y. Use `document.addEventListener('mousemove', e => document.title = e.clientX + ',' + e.clientY)` to capture exact coordinates when needed.

## Selecting a choice

Click the card text to open the choice preview popup, then click `确认选择` at approximately `x=720, y=548`.

## Other buttons

- **"好的" button**: Achievement popups — click at approximately `x=720, y=590`.
- **"继续" button**: Ending screens — click at approximately `x=436, y=764`.
- **"落笔" button**: Bottom-right corner of the screen — follow in-game prompts when this appears.
