# The Tyrrell Codex — AEGIS production workspace

**The Tyrrell Codex** = YouTube channel · **Ferrum Doctrine** = content series · Handle `@tyrrellkdlemons`

## Whereabouts (start here)

→ **[`WHERE.md`](WHERE.md)** — map of every important folder and the current upload pack.

## Current release (FD-001)

| Item | Path |
|------|------|
| Long-form | `platforms/youtube/FD-001_release/01_long.mp4` |
| Short | `platforms/youtube/FD-001_release/02_short.mp4` |
| Thumbnail | `platforms/youtube/FD-001_release/03_thumbnail.png` |
| Manifest | `platforms/youtube/FD-001_release/publish_manifest.json` |
| Master script | `content_core/cycles/FD-001_capability-protocol/01_master_script.md` |
| QA seal | `prometheus/v2_seal.json` |
| Clearance | `publish_clearance.json` |

Publication state: **locally ready, not uploaded**. Compatibility shims (`platforms/youtube/final_long.mp4`) still point at the same file.

## Directory contract

| Folder | What lives there |
|--------|------------------|
| `WHERE.md` | Human map / whereabouts |
| `control/` | Mirrors of task board, roles, clearance, logs |
| `content_core/cycles/FD-00N_*/` | Master scripts + specs per cycle |
| `platforms/<site>/FD-001_release/` | **Current** upload packs |
| `platforms/upcoming/FD-00N_*/` | Future cycles (002–004) |
| `dashboard/` → `docs/` | GitHub Pages dashboard |
| `prometheus/` | Visual/technical QA |
| `pipelines/` | Render + organize scripts |
| `archive/` | Pre-organize clutter |
| `assets/archive_legacy_renders/` | Old V1/Phoenix temp renders |

## Source of truth (order)

1. `WHERE.md` — whereabouts  
2. `task_board.json` / `control/task_board.json` — work state  
3. `active_roles.json` — locks & channel identity  
4. `content_core/00_INDEX.json` — cycle index  
5. `platforms/SCHEDULE.json` — post clock  
6. `platforms/*/FD-001_release/publish_manifest.json` — exact copy  
7. `prometheus/v2_seal.json` — inspected media seal  
8. `publish_clearance.json` — local vs external publish truth  

## Hard rules

- Ready means file exists, decodes, correct aspect, passed inspection — not a green status alone.  
- Published means a real platform URL exists.  
- No fabricated metrics, affiliates, or analytics.  
- Do **not** rename the YouTube channel again without a new direct user instruction.  
- Never put Ferrum Doctrine content on the children’s channel.

See `AGENT_HANDOFF.md` for the next-agent checklist and `SYSTEM_ARCHITECTURE.md` for the system dossier.
