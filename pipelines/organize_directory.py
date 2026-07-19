#!/usr/bin/env python3
"""
Codex-aligned directory reorganization for The Tyrrell Codex / Ferrum Doctrine.

Goals: readable names, obvious whereabouts, one current release pack, upcoming cycles.
Does not rename the YouTube channel.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def move(src: Path, dest: Path) -> str:
    if not src.exists():
        return f"SKIP missing: {src.relative_to(ROOT)}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if dest.is_dir() and src.is_dir():
            # merge files
            for child in src.iterdir():
                move(child, dest / child.name)
            try:
                src.rmdir()
            except OSError:
                pass
            return f"MERGE {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}"
        return f"SKIP exists: {dest.relative_to(ROOT)}"
    shutil.move(str(src), str(dest))
    return f"MOVE {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}"


def copy_if(src: Path, dest: Path) -> str:
    if not src.exists():
        return f"SKIP missing: {src}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dest.exists():
            return f"SKIP dir exists: {dest.relative_to(ROOT)}"
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    return f"COPY {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_json(path: Path, data: object) -> None:
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    log: list[str] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = ensure(ROOT / "archive" / f"pre_organize_{stamp}")

    # --- 1) Archive root clutter ---
    for name in [
        "_tts_probe.py",
        "_tts_test.mp3",
        "why_99_percent_men_never_dangerous_longTEMP_MPY_wvf_snd.mp4",
        "task_board_v2.json",
        ".aegis.lock",
    ]:
        src = ROOT / name
        if src.exists():
            log.append(move(src, archive / "root" / name))

    # --- 2) content_core → cycles/FD-00N ---
    cycles = ensure(ROOT / "content_core" / "cycles")
    mapping_scripts = {
        "FD-001_capability-protocol": {
            "master": ROOT / "content_core" / "master_script.md",
            "broll": ROOT / "content_core" / "broll_shot_list.md",
            "thumb_spec": ROOT / "content_core" / "thumbnail_spec.md",
            "thumb_img": ROOT / "content_core" / "thumbnail_final.png",
        },
        "FD-002_soft-habits": {
            "master": ROOT / "content_core" / "future" / "soft_habits_kill_ambition.md",
        },
        "FD-003_spy-room-read": {
            "master": ROOT / "content_core" / "future" / "spy_method_read_any_room.md",
        },
        "FD-004_mental-fortress": {
            "master": ROOT / "content_core" / "future" / "mental_fortress_digital_noise.md",
        },
    }

    for folder, files in mapping_scripts.items():
        dest_dir = ensure(cycles / folder)
        if "master" in files and files["master"].exists():
            log.append(move(files["master"], dest_dir / "01_master_script.md"))
        if files.get("broll") and files["broll"].exists():
            log.append(move(files["broll"], dest_dir / "02_broll_shots.md"))
        if files.get("thumb_spec") and files["thumb_spec"].exists():
            log.append(move(files["thumb_spec"], dest_dir / "03_thumbnail_spec.md"))
        if files.get("thumb_img") and files["thumb_img"].exists():
            log.append(move(files["thumb_img"], dest_dir / "thumbnail.png"))

    # brand guide rename
    brand = ROOT / "content_core" / "brand_style_guide.md"
    if brand.exists():
        log.append(move(brand, ROOT / "content_core" / "00_BRAND_STYLE.md"))

    # index rename
    idx = ROOT / "content_core" / "content_index.json"
    if idx.exists():
        log.append(move(idx, ROOT / "content_core" / "00_INDEX.json"))

    # remove empty future dir
    future = ROOT / "content_core" / "future"
    if future.exists():
        try:
            future.rmdir()
            log.append("RMDIR content_core/future")
        except OSError:
            log.append(move(future, archive / "content_core_future"))

    # --- 3) platforms/buffer → platforms/upcoming/FD-00N ---
    buffer = ROOT / "platforms" / "buffer"
    upcoming = ensure(ROOT / "platforms" / "upcoming")
    buf_map = {
        "ferrum-doctrine-002": "FD-002_soft-habits",
        "ferrum-doctrine-003": "FD-003_spy-room-read",
        "ferrum-doctrine-004": "FD-004_mental-fortress",
    }
    if buffer.exists():
        for old, new in buf_map.items():
            src = buffer / old
            if src.exists():
                log.append(move(src, upcoming / new))
        # leftover schedule/readme
        for leftover in buffer.iterdir():
            log.append(move(leftover, archive / "platforms_buffer" / leftover.name))
        try:
            buffer.rmdir()
            log.append("RMDIR platforms/buffer")
        except OSError:
            pass

    # --- 4) Current release pack: platforms/youtube → platforms/youtube/FD-001_release ---
    # Keep ALSO flat copies? Codex handoff points to platforms/youtube/final_long.mp4
    # Strategy: put canonical pack in FD-001_release AND keep short aliases at youtube/ root via copy of manifests + README pointers
    yt = ROOT / "platforms" / "youtube"
    release = ensure(yt / "FD-001_release")
    for name in [
        "final_long.mp4",
        "final_short.mp4",
        "thumbnail_final.png",
        "publish_manifest.json",
        "WHAT_WHERE_WHEN.md",
        "v2_upload_packet.json",
        "phoenix_concat.txt",
    ]:
        src = yt / name
        if src.exists() and not (release / name).exists():
            # Prefer move into release, then recreate stub pointer files for compatibility? 
            # User wants whereabouts — move into release, write ROOT youtube/README pointing there.
            log.append(move(src, release / name))

    # Standardize release media names inside pack
    renames = {
        "final_long.mp4": "01_long.mp4",
        "final_short.mp4": "02_short.mp4",
        "thumbnail_final.png": "03_thumbnail.png",
        "publish_manifest.json": "publish_manifest.json",
        "WHAT_WHERE_WHEN.md": "WHAT_WHERE_WHEN.md",
    }
    for old, new in renames.items():
        src = release / old
        dest = release / new
        if src.exists() and old != new:
            log.append(move(src, dest))

    # Compatibility shims at platforms/youtube/ for old paths (copy, not move)
    shim_long = release / "01_long.mp4"
    shim_short = release / "02_short.mp4"
    shim_thumb = release / "03_thumbnail.png"
    if shim_long.exists():
        log.append(copy_if(shim_long, yt / "final_long.mp4"))
    if shim_short.exists():
        log.append(copy_if(shim_short, yt / "final_short.mp4"))
    if shim_thumb.exists():
        log.append(copy_if(shim_thumb, yt / "thumbnail_final.png"))
    if (release / "publish_manifest.json").exists():
        log.append(copy_if(release / "publish_manifest.json", yt / "publish_manifest.json"))
    if (release / "WHAT_WHERE_WHEN.md").exists():
        log.append(copy_if(release / "WHAT_WHERE_WHEN.md", yt / "WHAT_WHERE_WHEN.md"))

    # Instagram / TikTok current release folders
    for plat, files in {
        "instagram": [("final_reel.mp4", "01_reel.mp4")],
        "tiktok": [("final_tiktok.mp4", "01_tiktok.mp4")],
        "x": [("thread.txt", "01_thread.txt")],
        "reddit": [("post.md", "01_post.md")],
    }.items():
        pdir = ROOT / "platforms" / plat
        rdir = ensure(pdir / "FD-001_release")
        for old, new in files:
            src = pdir / old
            if src.exists():
                log.append(move(src, rdir / new))
                log.append(copy_if(rdir / new, pdir / old))  # shim
        # move manifests if present
        for extra in ["publish_manifest.json", "WHAT_WHERE_WHEN.md", "caption.txt"]:
            src = pdir / extra
            if src.exists() and src.is_file():
                log.append(move(src, rdir / extra))
                log.append(copy_if(rdir / extra, pdir / extra))

    # --- 5) assets cleanup ---
    assets_final = ROOT / "assets" / "final"
    legacy = ensure(ROOT / "assets" / "archive_legacy_renders")
    if assets_final.exists():
        for p in assets_final.iterdir():
            name = p.name.lower()
            if name.startswith("why_99") or name.startswith("why_most") or name.startswith("ferrum_doctrine_001_phoenix") or name.startswith("."):
                log.append(move(p, legacy / p.name))

    # scripts archive
    scripts = ROOT / "assets" / "scripts"
    if scripts.exists():
        log.append(move(scripts, legacy / "old_scripts"))

    # --- 6) control/ folder for ops JSON at root (copies + pointers kept at root for Codex) ---
    control = ensure(ROOT / "control")
    for name in [
        "task_board.json",
        "active_roles.json",
        "publish_clearance.json",
        "style_manifest.json",
        "content_calendar.md",
        "comms_log.md",
        "session_log.md",
    ]:
        src = ROOT / name
        if src.exists():
            log.append(copy_if(src, control / name))

    # --- 7) pipelines rename for clarity ---
    pipe_renames = {
        "one_shot_cycle.py": "legacy_one_shot_cycle.py",
        "production_cycle_v2.py": "render_cycle_v2.py",
        "phoenix_render_and_buffer.py": "render_phoenix_and_buffer.py",
        "organize_directory.py": "organize_directory.py",
    }
    for old, new in pipe_renames.items():
        src = ROOT / "pipelines" / old
        dest = ROOT / "pipelines" / new
        if src.exists() and old != new and not dest.exists():
            log.append(move(src, dest))

    # --- 8) Write WHERE.md and update indexes ---
    where = f"""# WHERE THINGS LIVE — The Tyrrell Codex / Ferrum Doctrine

Channel: **The Tyrrell Codex** · Series: **Ferrum Doctrine** · Handle: `@tyrrellkdlemons`

Read this first when you need whereabouts. Generated: {stamp}

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

Old paths like `platforms/youtube/final_long.mp4` still exist as **copies** of the FD-001 release files so Codex handoff paths keep working. Prefer the `FD-001_release/` names going forward.

## Naming rules (going forward)

- Cycles: `FD-00N_short-kebab-slug`
- Release media: `01_long.mp4`, `02_short.mp4`, `03_thumbnail.png`
- Scripts: `01_master_script.md`, `02_broll_shots.md`, `03_thumbnail_spec.md`
- Never put AEGIS content on the children’s channel
"""
    write(ROOT / "WHERE.md", where)

    # Update content index
    index = {
        "schema_version": 3,
        "channel": {
            "name": "The Tyrrell Codex",
            "series": "Ferrum Doctrine",
            "youtube_channel_id": "UCh82kLGeSgdCd1VNEQsZ2pg",
            "handle": "@tyrrellkdlemons",
        },
        "whereabouts": "WHERE.md",
        "current_cycle": {
            "content_id": "FD-001",
            "folder": "content_core/cycles/FD-001_capability-protocol/",
            "master_script": "content_core/cycles/FD-001_capability-protocol/01_master_script.md",
            "youtube_release": "platforms/youtube/FD-001_release/",
            "status": "ready_local_not_published",
        },
        "upcoming": [
            {
                "content_id": "FD-002",
                "folder": "content_core/cycles/FD-002_soft-habits/",
                "platforms": "platforms/upcoming/FD-002_soft-habits/",
            },
            {
                "content_id": "FD-003",
                "folder": "content_core/cycles/FD-003_spy-room-read/",
                "platforms": "platforms/upcoming/FD-003_spy-room-read/",
            },
            {
                "content_id": "FD-004",
                "folder": "content_core/cycles/FD-004_mental-fortress/",
                "platforms": "platforms/upcoming/FD-004_mental-fortress/",
            },
        ],
    }
    write_json(ROOT / "content_core" / "00_INDEX.json", index)

    # youtube release README
    write(
        yt / "README.md",
        "# YouTube packs\n\n"
        "**Current upload:** `FD-001_release/`\n\n"
        "| File | Use |\n|------|-----|\n"
        "| `01_long.mp4` | Main upload |\n"
        "| `02_short.mp4` | Shorts |\n"
        "| `03_thumbnail.png` | Custom thumbnail |\n"
        "| `publish_manifest.json` | Title/description/tags |\n\n"
        "Root `final_long.mp4` is a compatibility shim of `FD-001_release/01_long.mp4`.\n",
    )

    write(
        upcoming / "README.md",
        "# Upcoming cycles (not yet the current release)\n\n"
        "- `FD-002_soft-habits/`\n"
        "- `FD-003_spy-room-read/`\n"
        "- `FD-004_mental-fortress/`\n\n"
        "Each folder has youtube/instagram/tiktok/x packs.\n",
    )

    # Update publish_clearance paths
    clearance_path = ROOT / "publish_clearance.json"
    if clearance_path.exists():
        try:
            c = json.loads(clearance_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            c = {}
        c["schema_version"] = max(int(c.get("schema_version", 2)), 3)
        c["whereabouts"] = "WHERE.md"
        c["evidence"] = c.get("evidence") or {}
        c["evidence"]["long_form"] = "platforms/youtube/FD-001_release/01_long.mp4"
        c["evidence"]["thumbnail"] = "platforms/youtube/FD-001_release/03_thumbnail.png"
        c["evidence"]["qa_seal"] = "prometheus/v2_seal.json"
        c["note"] = (
            "Local files ready for operator upload. Canonical pack is "
            "platforms/youtube/FD-001_release/. Compatibility shims remain at platforms/youtube/final_*.mp4."
        )
        write_json(clearance_path, c)
        log.append(copy_if(clearance_path, control / "publish_clearance.json"))

    # Patch youtube publish_manifest file fields
    man = release / "publish_manifest.json"
    if man.exists():
        try:
            m = json.loads(man.read_text(encoding="utf-8"))
            m["file"] = "01_long.mp4"
            m["secondary_files"] = ["02_short.mp4"]
            m["thumbnail"] = "03_thumbnail.png"
            m["pack_path"] = "platforms/youtube/FD-001_release/"
            write_json(man, m)
            log.append(copy_if(man, yt / "publish_manifest.json"))
        except json.JSONDecodeError:
            pass

    # SCHEDULE path updates
    sched_path = ROOT / "platforms" / "SCHEDULE.json"
    if sched_path.exists():
        try:
            s = json.loads(sched_path.read_text(encoding="utf-8"))
            for post in s.get("posts", []):
                f = post.get("file", "")
                f = f.replace("platforms/buffer/ferrum-doctrine-002", "platforms/upcoming/FD-002_soft-habits")
                f = f.replace("platforms/buffer/ferrum-doctrine-003", "platforms/upcoming/FD-003_spy-room-read")
                f = f.replace("platforms/buffer/ferrum-doctrine-004", "platforms/upcoming/FD-004_mental-fortress")
                f = f.replace("platforms/youtube/final_long.mp4", "platforms/youtube/FD-001_release/01_long.mp4")
                post["file"] = f
            write_json(sched_path, s)
        except json.JSONDecodeError:
            pass

    # reorganization log
    write(ROOT / "archive" / f"organize_log_{stamp}.md", "# Organize log\n\n" + "\n".join(f"- {x}" for x in log) + "\n")
    write(ROOT / "pipelines" / "_last_organize_log.txt", "\n".join(log) + "\n")
    print(f"Done. {len(log)} ops. See WHERE.md")


if __name__ == "__main__":
    main()
