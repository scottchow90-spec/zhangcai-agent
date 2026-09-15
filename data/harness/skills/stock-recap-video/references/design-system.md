# Stock recap video design system v2

## Editorial direction

- Default to a premium financial-newsroom look: deep navy canvas, high-contrast typography, procedural market graphics, and restrained cinematic depth.
- Every business scene must have its own visual grammar. Reusing one title-and-card shell across the full video is a rejection condition.
- Create `public/storyboard.json` before rendering. Each of at least five business scenes must declare one purpose, one focal idea, one distinct visualization, one transition, and at least three motion layers.
- External visual assets are optional. Prefer self-created SVG charts, heatmaps, flows, rings, grids, and typographic composition so licensing remains deterministic.

## Frame and type

- Vertical default: 1080x1920 at 30 fps; fixed short-form timeline: 70 seconds.
- Safe area: 72-80 px left/right and 118-150 px top/bottom. Captions occupy the lower 300 px.
- Headline 76-104 px; dominant number 70-150 px; supporting text 28-42 px; captions 44-52 px.
- Use Microsoft YaHei or Noto Sans SC. No visible text below 20 px; no more than three simultaneous focal elements.

## Color and depth

- Canvas `#071018`; navy `#0B1723`; panel `#102333`; text `#F5FAFC`; muted `#9EB1BE`.
- Signal red `#FF6470`; market green `#35D399`; cyan `#41D9E6`; amber `#F4BE5B`.
- Use red/green with arrows or labels so color is never the only encoding.
- Subtle linear/radial gradients, soft glows, grids, and transparent depth layers are allowed when they clarify hierarchy. Reject decorative blobs, gaudy neon, or low-contrast glass effects.

## Motion grammar

- Use `useCurrentFrame()`, `interpolate()`, SVG path progress, and Remotion `TransitionSeries`; never CSS animations.
- Every business scene needs at least three motion layers: one structural movement, one data reveal, and one ambient continuous movement.
- Entrances alone do not qualify as video motion. One-second within-scene sampling must produce an overall static-pair ratio no higher than 0.35, mean pixel difference at least 0.55, and no individual scene above 0.60 static pairs.
- Keep transitions 12-18 frames. Prefer fade for conceptual continuity and directional slide for a change in analytical layer.

## Captions and rhythm

- First 5 seconds: exact dedicated risk notice, silent, with no business content.
- Business sequence: hook, breadth, main-line capital flow, conditional scenario, execution close.
- Caption pages contain 4-20 normalized Chinese characters and at most two lines. Use an editorial lower-third with a single accent rule, not a thick outline box.
- Closing scene includes AI-voice disclosure and source-cutoff language.

## Visual technical prefilter

- Inspect a six-frame contact sheet covering risk notice and all five business scenes.
- Fill the hash-bound eight-dimension internal scorecard: composition, typography, color depth, motion, data visualization, rhythm, caption integration, and brand coherence.
- Every score must be 8-10. Any dimension below 8, any mojibake, clipping, overlap, blank scene, static-slide behavior, repeated scene shell, unreadable caption, or unlicensed asset blocks delivery.
- The business-scene samples must also keep mean lower-40-percent edge ratio at or above 0.018 and mean lower-40-percent low-information-row ratio at or below 0.65; otherwise the composition is rejected as bottom-heavy dead space.
- This scorecard can reject a candidate but cannot prove user-perceived polish. An explicit user rejection overrides it and sends the same workflow back to redesign.
