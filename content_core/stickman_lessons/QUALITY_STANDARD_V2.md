# Stickman Forge — Quality Standard V2

## Benchmark (what big stickman Shorts / Reels do)

Viral stickman fight channels and CapCut fight-edit trends win on:

1. **Continuous motion** — limbs interpolate; never 4 frozen slides
2. **Impact language** — flash frames, screen shake, speed lines, hit bursts
3. **Kinetic captions** — 2–5 words slamming on beat (not paragraph overlays)
4. **Sound design** — whoosh / hit / sting under VO (silence between cuts kills retention)
5. **Short runtime** — ~15–35s; hook in first second
6. **Atmosphere** — vignette, arena depth, glow — not flat black PowerPoint

## V1 failure mode (rejected)

- 4 pose holds with hard cuts
- Paragraph captions
- VO only, no SFX
- ~55s soft pacing
- ~500KB thin encodes that feel like slides

## V2 delivery (this cycle)

| Spec | Value |
|------|-------|
| Engine | `pipelines/stickman_forge.py` (V2) |
| Size | 1080×1920 |
| FPS | 30 |
| Encode | H.264 CRF 16, AAC 256k |
| Motion | Pose lerp + afterimages |
| FX | Shake, flash, speed lines, bursts |
| Audio | Edge TTS + procedural SFX mix |
| Captions | Beat-synced kinetic titles |

## Upgrade path (blocked until auth)

Higgsfield **Nano Banana** (character stills) → **Seedance 2.0** (image-to-video fight plates) would match the 2026 AI-stickman meta. Requires:

```bash
higgsfield auth login
```

Until then, V2 local cinematic is the production bar for Authoritas review.
