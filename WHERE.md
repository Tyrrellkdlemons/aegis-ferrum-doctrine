# WHERE THINGS LIVE — The Tyrrell Codex / Ferrum Doctrine

Channel: **The Tyrrell Codex** · Series: **Ferrum Doctrine** · Handle: `@tyrrellkdlemons`

Read this first when you need whereabouts. Generated: 20260719T020301Z

## Start here

| Need | Go to |
|------|--------|
| What to do next | `control/task_board.json` (mirror: `task_board.json`) |
| Who owns what | `control/active_roles.json` |
| Can we upload? | `control/publish_clearance.json` |
| Master scripts by cycle | `content_core/cycles/FD-00N_*/01_master_script.md` |
| **Upload TODAY (YT)** | `platforms/youtube/FD-001_release/01_long.mp4` |
| Thumbnail TODAY | `platforms/youtube/FD-001_release/03_thumbnail.png` |
| Upcoming videos | `platforms/upcoming/FD-00N_*/` |
| QA seal | `prometheus/v2_seal.json` |
| Dashboard source | `dashboard/` → published from `docs/` |
| Live dashboard | `https://tyrrellkdlemons.github.io/aegis-ferrum-doctrine/` |
| Brand rules | `content_core/00_BRAND_STYLE.md` |
| Full index | `content_core/00_INDEX.json` |
| Old junk | `archive/` and `assets/archive_legacy_renders/` |

## Directory map

```text
Man Youtube/
├── WHERE.md                 ← you are here
├── README.md                ← project contract (Codex)
├── AGENT_HANDOFF.md         ← next-agent checklist
├── SYSTEM_ARCHITECTURE.md
├── control/                 ← ops mirrors (task board, clearance, logs)
├── content_core/
│   ├── 00_INDEX.json
│   ├── 00_BRAND_STYLE.md
│   └── cycles/
│       ├── FD-001_capability-protocol/
│       ├── FD-002_soft-habits/
│       ├── FD-003_spy-room-read/
│       └── FD-004_mental-fortress/
├── platforms/
│   ├── SCHEDULE.json
│   ├── youtube/FD-001_release/   ← CURRENT upload pack
│   ├── instagram/FD-001_release/
│   ├── tiktok/FD-001_release/
│   ├── x/FD-001_release/
│   ├── reddit/FD-001_release/
│   └── upcoming/                 ← FD-002..004 buffer
├── assets/                  ← working media (voice, visuals, archives)
├── prometheus/              ← QA / veto
├── pipelines/               ← render & organize scripts
├── dashboard/ + docs/       ← GitHub Pages
├── research/
├── monetization/
└── archive/                 ← pre-organize clutter
```

## Cycle IDs (stable)

| ID | Slug folder | Topic |
|----|-------------|--------|
| FD-001 | capability-protocol | Current release — capability / edge protocol |
| FD-002 | soft-habits | Soft habits that kill ambition |
| FD-003 | spy-room-read | Spy method room read |
| FD-004 | mental-fortress | Mental fortress vs digital noise |

## Compatibility shims

Old paths like `platforms/youtube/final_long.mp4` still exist as **copies** of the FD-001 release files so Codex handoff paths keep working. Prefer the `FD-001_release/` names going forward. The legacy files under `assets/archive_legacy_renders/` are archive material, not release inputs.

## Current gate

- FD-001: local media cleared, not uploaded.
- FD-002: full master complete; existing media requires re-render and Prometheus review.
- FD-003/004: outlines only; existing media remains on QA hold.
- Dashboard: GitHub Pages deployment source is `docs/`; live build verified at `https://tyrrellkdlemons.github.io/aegis-ferrum-doctrine/`.

## Naming rules (going forward)

- Cycles: `FD-00N_short-kebab-slug`
- Release media: `01_long.mp4`, `02_short.mp4`, `03_thumbnail.png`
- Scripts: `01_master_script.md`, `02_broll_shots.md`, `03_thumbnail_spec.md`
- Never put AEGIS content on the children’s channel

## Stickman Forge (short-form combat lessons)

| Need | Path |
|------|------|
| Scripts | content_core/stickman_lessons/scripts/lesson_01.md … lesson_10.md |
| Index | content_core/stickman_lessons/CYCLE_001_INDEX.json |
| MP4s (9:16) | ssets/final/stickman/lesson_01.mp4 … lesson_10.mp4 |
| YouTube Shorts manifests | platforms/youtube_shorts/lesson_XX/ |
| Reels manifests | platforms/instagram_reels/lesson_XX/ |
| TikTok manifests | platforms/tiktok/stickman/lesson_XX/ |
| Renderer | pipelines/stickman_forge.py |

Status: **review** — notify Authoritas before Publicator uploads.

