# AEGIS Agent Handoff

## Read first

Read `README.md`, `SYSTEM_ARCHITECTURE.md`, `task_board.json`, `comms_log.md`, `style_manifest.json`, and `prometheus/last_seal.json` before changing task state.

## Verified external state

- The signed-in YouTube Studio account was verified against the user-designated account during the 2026-07-18 session.
- The one authorized channel-name change was saved as **The Tyrrell Codex**.
- The YouTube handle was deliberately left unchanged because the user authorized a name change, not a handle change.
- Do not rename the channel again without a new direct user instruction.

## Current production status

The first local pipeline generated attractive-sounding status records but low-quality template visuals and a heuristic “99” thumbnail score. Its long-form render failed and produced a zero-byte output. Treat that original seal as invalidated.

V2 is complete: a 6:38.96 long-form video, three dedicated 9:16 adaptations, 12 original scene images, and a final thumbnail. The evidence-based V2 seal is `prometheus/v2_seal.json` (87/100); the inspection record is `prometheus/qa_report_v2.md`. Do not substitute the original zero-byte/placeholder assets or the center-cropped short with clipped captions.

A separate Phoenix process wrote conflicting Ferrum Doctrine status files and an unverified heuristic seal. Those files were preserved, but V2 uses namespaced status and upload manifests (`task_board_v2.json`, `prometheus/v2_seal.json`, and `platforms/youtube/v2_upload_packet.json`) so the evidence is not overwritten.

## Continuation order

1. Obtain the required action-time confirmation immediately before uploading the local V2 video to YouTube.
2. Reclaim the Chrome handoff tab already staged at the YouTube Studio `Select files` dialog for channel ID `UCh82kLGeSgdCd1VNEQsZ2pg`.
3. Upload the long-form video and thumbnail from the paths in `platforms/youtube/v2_upload_packet.json`.
4. Select **No, not made for kids** and **Yes, altered/synthetic content**. Do not add affiliate links, a lead magnet, or a paid-promotion claim.
5. Publish or schedule only after YouTube's checks complete, then record the final URL.

## Non-negotiables

- No fabricated trend numbers, analytics, revenue, product conversions, or visual scores.
- No CAPTCHA bypass, proxy rotation, cookie extraction, fake engagement, unsolicited spam, or subreddit-rule evasion.
- No copied celebrity footage, cloned third-party voices, unlicensed music, or competitor thumbnail duplication.
- “Autonomous” never removes provenance, policy, or quality gates.
