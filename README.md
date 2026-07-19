# The Tyrrell Codex — AEGIS Production Workspace

This workspace is the production control plane for a YouTube-first channel about discipline, applied Stoicism, attention, technology, strategy, and practical self-command.

## Current cycle

- Channel name: **The Tyrrell Codex** (the authorized one-time name change was saved in YouTube Studio on 2026-07-18).
- Active episode: **Why 99% of Men Will Never Be Dangerous (And How You Become the 1%)**.
- Editorial definition: “dangerous” means calm capability and constructive options under pressure—not aggression, intimidation, or violence.
- Publication state: **blocked pending a finished media render and real QA**. A zero-byte local render and a template-based Prometheus score are not publishable evidence.

## Source of truth

1. `task_board.json` — task state and dependencies.
2. `comms_log.md` — append-only operational record.
3. `content_calendar.md` — planned topics and dates.
4. `style_manifest.json` — visual and audio constraints.
5. `prometheus/last_seal.json` — last automated score; never treat it as sufficient without visual inspection.
6. `assets/final/*_publish_packet.json` — metadata only after the matching media file passes validation.

## Publish gate

An upload may proceed only when all of the following are true:

- The rendered file exists, is non-empty, opens successfully, has audio and video streams, and matches the intended aspect ratio.
- The script has a distinct thesis, original commentary, practical value, and source notes for factual claims.
- The thumbnail and sampled video frames pass human visual inspection; a heuristic contrast score alone cannot issue a seal.
- Generated or meaningfully altered realistic media is disclosed in YouTube Studio when required.
- Music, footage, images, and voices are original, licensed, or otherwise cleared.
- Metadata is accurate and does not promise a resource, affiliate offer, or product that does not exist.

See `SYSTEM_ARCHITECTURE.md` for the academic exhibition dossier and `AGENT_HANDOFF.md` for continuation instructions.
