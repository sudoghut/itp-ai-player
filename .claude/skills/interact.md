---
name: interact
description: Card interaction coordinates and UI button positions for the ITP game canvas
trigger: when performing hover, click, or UI interactions on the game canvas
---

# Choice Card Interaction

During story mode, choices appear as wooden card tags at the bottom of the canvas. Each card has a single Chinese character written on it (e.g. `入`, `出`, `戒`).

## Hover to reveal tooltip

Move the mouse onto the **character text** on the card to reveal a tooltip with the choice title and description. Hovering between cards or on the card edges does NOT trigger the tooltip. The hotzone is very small — must be precise.

## Card text positions (1440x900 canvas)

Card positions **vary between scenes**. The coordinates below are approximate centers. Use the spiral hover technique (see below) to handle variance.

### Three-card layout (verified ranges)
- Left card text: `x=350-400, y=670-730`
- Middle card text: `x=670-740, y=670-710`
- Right card text: `x=1030-1070, y=670-710`

### Four-card layout
- Card 1: `x=384, y=642`
- Card 2: `x=608, y=703`
- Card 3: `x=810, y=730`
- Card 4: `x=1080, y=730`

## Spiral hover technique

Card hotspots are very small (~10-20px) and shift between scenes. Instead of a single hover at one point, use a spiral pattern of `move` commands (no click) around the estimated center to increase hit rate:

```
For a center point (cx, cy), move through these offsets:
(cx, cy), (cx+10, cy), (cx+10, cy+10), (cx, cy+10), (cx-10, cy+10),
(cx-10, cy), (cx-10, cy-10), (cx, cy-10), (cx+10, cy-10),
(cx+20, cy), (cx+20, cy+20), (cx, cy+20), (cx-20, cy+20),
(cx-20, cy), (cx-20, cy-20), (cx, cy-20), (cx+20, cy-20)
```

Use ~200ms delay between each move. After the spiral, take a screenshot to check if the tooltip appeared. This covers a 40x40px area around the center.

### Known successful coordinates (verified via mousemove listener)
- 1116 scene: left=384,673 / middle=723,675 / right=1063,711
- 1121 scene: left=384,681 / middle=731,676 / right=1068,677

## Selecting a choice

Click the card text to open the choice preview popup, then click `确认选择` at approximately `x=720, y=548`.

**To cancel a selection preview**: click far outside the popup (e.g. `x=1400, y=50` or `x=200, y=850`). Escape key does NOT work.

## Other buttons

- **"好的" button**: Achievement popups — click at approximately `x=720, y=590`.
- **"继续" button**: Ending screens — click at approximately `x=436, y=764`.
- **"落笔" button**: Bottom-right corner of the screen — follow in-game prompts when this appears.
