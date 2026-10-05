---
name: stock-recap-video
description: Generate polished narrated stock-market recap videos as MP4 with evidence-bound data, a dedicated opening risk notice, motion graphics, charts, Chinese captions, AI voiceover, and deterministic audiovisual quality gates. Use for 股票复盘视频, A股收盘复盘短视频, 涨停复盘视频, narrated market recap, landscape or vertical stock video, or when Codex must create, revise, or verify a stock-related video file.
---

# 股票复盘视频

Produce stock videos through one fixed route: a selected local stock-research skill for business truth, OpenAI `speech` for narration, Remotion for visuals, and FFmpeg/FFprobe plus the central stock risk gate for acceptance.

## Non-negotiable route

1. Inventory installed stock skills and select the exact business skill before research. Execute its fixed entry and read back the persisted result. Do not invent market facts in the video layer.
2. Use fresh market evidence and keep facts, inferences, scenarios, risks, and unavailable data distinguishable in the script.
3. Create the project only with `scripts/codex_entry.py run -- create`. Patch and rerun this template; do not switch authoring stacks.
4. Generate narration through `$speech` and its bundled CLI first. Use `cedar` by default with a composed, evidence-first tone. If the live API is unavailable or rejects authentication, the fixed `run -- voiceover --provider auto` command may fall back to the installed Chinese Windows SAPI voice; record the actual provider and disclose synthetic/AI voice in the video.
5. Create and approve `public/storyboard.json` through `run -- storyboard` before rendering. Rendering fails closed unless the current storyboard receipt proves five distinct scene grammars and three motion layers per scene.
6. Render only through `scripts/codex_entry.py run -- render`. It pins the template dependencies, verifies the storyboard receipt, invokes Remotion, and embeds the storyboard hash in the MP4.
7. Generate representative frames with `run -- visual-qa`, inspect its contact sheet, fill the generated eight-dimension internal technical prefilter, explicitly approve the required visual checks, and verify that receipt. The motion gate fails when the video behaves like static slides, and the density gate fails when the lower frame remains materially empty.
8. Validate only through `scripts/codex_entry.py run -- gate` with the current script, captions, visual receipt, and storyboard receipt; then run the central `$stock-delivery-risk-gate` `gate` and `verify-receipt` for the MP4. A failed or stale receipt blocks delivery.

## Production contract

- Default short-video format: 1080x1920, 30 fps, H.264 High, AAC 48 kHz, 60-120 seconds.
- Landscape format: 1920x1080 only when requested.
- Reserve the first 5 seconds exclusively for the exact central stock risk notice. Start all business content and narration after it.
- Keep essential text at least 80 px from the sides and 120 px from the top/bottom in a 1080-wide vertical frame. Reserve the lower 320 px for captions.
- Use one focal idea per scene. Each scene needs a distinct visualization and at least three motion layers; a repeated title-and-card shell is invalid.
- Treat the scorecard as an internal rejection filter only. It never proves that a video is polished, premium, or accepted by the user. Any explicit user rejection overrides every self-authored score and requires another visual pass.
- Use a restrained newsroom palette with subtle depth gradients, grids, and procedural SVG data graphics. Red and green must never be the only encoding of meaning.
- Animate by `useCurrentFrame()` and `interpolate()`; do not use CSS animations or transitions.
- Burn Chinese captions into the video. Keep each page to 4-20 normalized characters and no more than two lines.
- Music is optional and must remain below speech. Do not use unlicensed music or sound effects.

Read `references/design-system.md` when designing or revising scenes. Read the installed Remotion references for markup, captions, audio, timing, and rendering.

## Fixed entry

```powershell
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py info
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py selftest
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- create --project <project-dir>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- voiceover --project <project-dir> --input <script.txt> --instructions <voice-directions.txt> --provider auto
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- transcribe --project <project-dir> --out <transcript.txt>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- storyboard --project <project-dir>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- verify-storyboard-receipt --project <project-dir>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- render --project <project-dir> --out <video.mp4>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- visual-qa --video <video.mp4> --out-dir <visual-qa-dir> --receipt <visual-receipt.json>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- approve-visual --receipt <visual-receipt.json> --scorecard <aesthetic-scorecard.json> --reviewed-by codex-agent --confirm all-scenes-sampled,risk-notice-legible,no-clipping,no-overlap,no-blank-scene,caption-safe-area,visual-hierarchy,color-and-contrast
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- verify-visual-receipt --receipt <visual-receipt.json>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- gate --video <video.mp4> --script <script.txt> --captions <captions.json> --visual-receipt <visual-receipt.json> --storyboard-receipt <storyboard-receipt.json> --receipt <video-receipt.json>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py run -- verify-receipt --video <video.mp4> --receipt <video-receipt.json>
python D:\C盘转移\日志\codex\skills\stock-recap-video\scripts\codex_entry.py verify --receipt <统一门面回执.json>
```

## Required inputs

Before rendering, require:

- `public/voiceover.mp3`: final AI narration.
- `public/voiceover-receipt.json`: provider, script hash, voiceover hash, voice, and generation timestamp created only by the fixed voiceover command.
- `public/captions.json`: timestamped caption objects.
- `public/storyboard.json` and current `storyboard-receipt.json`: scene grammar, motion layers, transitions, and art direction.
- `public/video-metadata.json`: business-skill name, trade date, evidence SHA-256, script SHA-256, AI-voice disclosure, and source timestamps.
- `src/content.ts`: scene copy and chart values derived from the accepted business result.

## Acceptance

The fixed gates plus same-artifact visual and semantic QA must prove all of the following on the final MP4:

- playable video and audio streams; requested dimensions; 30 fps; H.264/AAC; `yuv420p`; fast-start metadata;
- first 5 seconds reserved for the exact risk notice and business content starts afterward;
- current evidence SHA-256 and `STOCK_DATA_TRADE_DATE` are embedded in MP4 metadata;
- narration is present, non-silent, normalized within the configured loudness window, and starts after the risk notice;
- no black opening/closing frame, long freeze, unexpected silence, or subtitle-safe-area violation;
- representative frames from every scene are extracted and visually inspected; within-scene static-pair ratio is at most 0.35, mean lower-40-percent edge ratio is at least 0.018, mean lower-40-percent low-information-row ratio is at most 0.65, and all eight internal prefilter scores are at least 8;
- local constrained Chinese speech-recognition readback materially matches every accepted script phrase; the installed OpenAI `transcribe` route is available for an additional unconstrained cloud readback when live credentials work;
- the final video receipt and central stock-risk receipt both match the current MP4 SHA-256.

Do not call a video polished merely because the agent-authored prefilter passes. Do not call it complete when any listed technical or risk layer is unverified.
