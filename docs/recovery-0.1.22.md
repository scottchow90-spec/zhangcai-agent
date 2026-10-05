# 0.1.22 recovery provenance

This branch is intended to recover the program layer shipped in the Windows updater
`掌财桌面端-程序更新-0.1.22-x64.exe` on top of Git commit
`89bbbb1a05e113772e82b963751fdbfddeb964f6` (`web-3003-14-skill-adapters`).

## Exact recovery

The updater preserved the following as source/plain text and they are restored from the
0.1.22 payload: `agent-server.mjs`, `scripts/`, `lib/`, `config/`, `harness-skills/`,
`public/`, `harness-headless.patch.yml`, Electron `main.mjs`/`preload.cjs`/
`runtime-ports.mjs` plus the new `tdx-root.mjs`, and the embedded formula/resource seed.

The updater also contains the exact 0.1.22 compiled Vinext `dist/`; it is restored as
release evidence and as a packaging fallback.

## Front-end source limitation

The program updater does not contain the original React/TSX source files such as
`app/home-client.tsx`, `app/chat/chat-client.tsx`, or `app/workspace-pages.tsx`, and no
source maps were found. Those source files therefore remain the 0.1.18 source baseline
until their 0.1.22 changes are reconstructed from the compiled bundle and validated.
The compiled 0.1.22 `dist/` must not be described as original TSX source.

## Version synchronization

The product version is restored to `0.1.22`. Packaged runtime/package metadata that was
still reporting `0.1.12`/`0.1.13`/`0.1.18` is synchronized by the recovery script.

The private runtime baseline is deliberately kept at `0.1.9`. Repository documentation
states that 0.1.9 rebuilt the runtime after the YAML dependency-pruning repair and later
program updates reuse that baseline. The program release version and runtime baseline
are separate version domains.

## Large skill archive

The 0.1.22 updater includes
`skill-archives/A股行情资讯全接口与数据能力大全_WorkBuddy电脑版_20260908-014459.zip`
(~145.6 MB). It was absent from the 0.1.18 Git tree and is larger than GitHub's ordinary
100 MB per-file limit, so it must be published through Git LFS or a GitHub Release asset.
The other 13 Skill14 ZIP archives match the 0.1.18 repository byte-for-byte.
