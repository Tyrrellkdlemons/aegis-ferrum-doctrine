# Prometheus QA

Prometheus is a veto protocol, not a magic score.

## Required evidence

- Technical probe: readable container, video stream, audio stream, duration, resolution, frame rate, and non-zero size.
- Audio review: narration intelligibility, no clipping, music below speech, no silent gaps or accidental truncation.
- Visual review: thumbnail legibility at small size, scene relevance, artifact check, sufficient visual change, and caption safe margins.
- Editorial review: original argument, factual support, no unsafe drills, no manipulative or demeaning framing.
- Rights and disclosure review: provenance for every asset and the correct altered/synthetic-content selection.

## Score policy

The “Operative Score” is a weighted checklist recorded in `prometheus/scoring/operative_score_rubric.md`. Any hard failure yields **VETO** regardless of the numeric total. Automated contrast, palette, and sharpness measurements may contribute no more than 15 points because they cannot judge meaning, originality, or truth.

`last_seal.json` must include the reviewer, inspected file hashes, technical probe, sampled timestamps, score components, hard-failure results, and notes. A record containing only an aggregate score is invalid.
