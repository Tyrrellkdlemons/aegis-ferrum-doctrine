#!/usr/bin/env python3
"""Pack operator state into dashboard/data and mirror to docs/ for Pages + Netlify."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
DOCS = ROOT / "docs"
DATA = DASH / "data"


def load(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    now = datetime.now(timezone(timedelta(hours=-7))).strftime("%Y-%m-%dT%H:%M:%S-07:00")

    schedule = load(DATA / "schedule.json", {})
    task_board = load(ROOT / "task_board.json", {})
    roles = load(ROOT / "active_roles.json", {})
    clearance = load(ROOT / "publish_clearance.json", {})
    index = load(ROOT / "content_core" / "00_INDEX.json", {})
    yt_manifest = load(ROOT / "platforms" / "youtube" / "FD-001_release" / "publish_manifest.json", {})
    seal = load(ROOT / "prometheus" / "v2_seal.json", {})
    stickman = load(ROOT / "content_core" / "stickman_lessons" / "CYCLE_001_INDEX.json", {})

    commands = [
        {
            "id": "validate",
            "label": "Validate release",
            "shell": "python pipelines/validate_release.py",
            "purpose": "Confirm manifests, media streams, hashes, dashboard parity.",
        },
        {
            "id": "sync_dashboard",
            "label": "Sync command center data",
            "shell": "python pipelines/sync_dashboard.py",
            "purpose": "Rebuild dashboard/data from task board, clearance, and seals; mirror to docs/.",
        },
        {
            "id": "stickman_v2",
            "label": "Render Stickman lesson",
            "shell": "python pipelines/stickman_forge.py lesson_01",
            "purpose": "Rebuild one Stickman Forge V2 short (swap lesson_id).",
        },
        {
            "id": "production_v2",
            "label": "Render long-form V2",
            "shell": "python pipelines/production_cycle_v2.py",
            "purpose": "Full V2 long-form production cycle (voice, scenes, captions).",
        },
        {
            "id": "deploy_pages",
            "label": "Deploy GitHub Pages",
            "shell": "git add docs dashboard && git commit -m \"Update command center\" && git push origin master",
            "purpose": "Push docs/ mirror so GitHub Pages rebuilds.",
        },
        {
            "id": "deploy_netlify",
            "label": "Deploy Netlify",
            "shell": "npx netlify-cli deploy --prod --dir=docs",
            "purpose": "Publish the same static board to the unique Netlify URL.",
        },
    ]

    upload_helper = {
        "channel": "The Tyrrell Codex",
        "channel_id": "UCh82kLGeSgdCd1VNEQsZ2pg",
        "handle": "@tyrrellkdlemons",
        "studio_url": "https://studio.youtube.com/channel/UCh82kLGeSgdCd1VNEQsZ2pg/videos/upload?d=ud",
        "pack": "platforms/youtube/FD-001_release/",
        "files": [
            "platforms/youtube/FD-001_release/01_long.mp4",
            "platforms/youtube/FD-001_release/03_thumbnail.png",
            "platforms/youtube/FD-001_release/02_short.mp4",
        ],
        "title": yt_manifest.get("title"),
        "description": yt_manifest.get("description"),
        "tags": yt_manifest.get("tags", []),
        "checks": [
            "Confirm Google account + channel ID before selecting files",
            "Audience: No, not made for kids",
            "Altered / synthetic content: YES",
            "No affiliate links / paid promotion claims",
            "Mid-roll OFF (under 8 minutes)",
            "Do not mark published until YouTube returns a real URL",
        ],
        "card": "platforms/youtube/FD-001_release/OPERATOR_UPLOAD_CARD.md",
    }

    tasks = task_board.get("tasks", [])
    progress = {
        "complete": sum(1 for t in tasks if t.get("status") == "complete"),
        "ready": sum(1 for t in tasks if "ready" in str(t.get("status", ""))),
        "review": sum(1 for t in tasks if t.get("status") in {"review", "rework", "review_rules_before_posting"}),
        "blocked": sum(1 for t in tasks if "blocked" in str(t.get("status", "")) or "awaiting" in str(t.get("status", ""))),
        "total": len(tasks),
    }

    command_center = {
        "schema_version": 1,
        "generated_at": now,
        "identity": {
            "channel": roles.get("channel", {}).get("name", "The Tyrrell Codex"),
            "series": roles.get("channel", {}).get("series", "Ferrum Doctrine"),
            "channel_id": roles.get("channel", {}).get("channel_id", "UCh82kLGeSgdCd1VNEQsZ2pg"),
            "handle": roles.get("channel", {}).get("handle", "@tyrrellkdlemons"),
        },
        "links": {
            "github_pages": "https://tyrrellkdlemons.github.io/aegis-ferrum-doctrine/",
            "netlify": "https://tyrrell-codex-aegis-command.netlify.app/",
            "netlify_admin": "https://app.netlify.com/projects/tyrrell-codex-aegis-command",
            "github_repo": "https://github.com/Tyrrellkdlemons/aegis-ferrum-doctrine",
            "youtube_studio": upload_helper["studio_url"],
        },
        "summary": schedule.get("summary", {}),
        "progress": progress,
        "tasks": tasks,
        "roles": roles.get("roles", {}),
        "clearance": clearance,
        "prometheus": schedule.get("prometheus") or {
            "visual_score": seal.get("operative_score"),
            "threshold": seal.get("publish_threshold"),
            "thumbnail_score": seal.get("thumbnail_score"),
            "thumbnail_threshold": seal.get("thumbnail_threshold"),
            "decision": "PASS" if seal.get("status") == "clear_for_upload" else seal.get("status"),
            "seal": "prometheus/v2_seal.json",
        },
        "content_index": index,
        "stickman": stickman,
        "commands": commands,
        "upload_helper": upload_helper,
        "editorial_intensity": schedule.get("editorial_intensity", {}),
        "posts": schedule.get("posts", []),
        "content": schedule.get("content", []),
        "performance": schedule.get("performance", {}),
        "timezone": schedule.get("timezone", "America/Los_Angeles"),
        "updated_at": schedule.get("updated_at", now),
    }

    # Keep schedule.json as the lightweight calendar source; command_center is the helper brain.
    write(DATA / "command_center.json", command_center)
    if schedule:
        schedule["updated_at"] = schedule.get("updated_at") or now
        schedule["deploy"] = command_center["links"]
        write(DATA / "schedule.json", schedule)

    # Mirror static site → docs for GitHub Pages + Netlify publish root
    DOCS.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "app.js", "styles.css"):
        src = DASH / name
        if src.is_file():
            shutil.copy2(src, DOCS / name)
    docs_data = DOCS / "data"
    if docs_data.exists():
        shutil.rmtree(docs_data)
    shutil.copytree(DATA, docs_data)

    # Preserve Pages config
    cfg = DOCS / "_config.yml"
    if not cfg.exists():
        cfg.write_text(
            "title: AEGIS Command — The Tyrrell Codex\n"
            "description: Operator command center for Ferrum Doctrine\n",
            encoding="utf-8",
        )

    print(f"Synced command center -> {DATA / 'command_center.json'}")
    print(f"Mirrored dashboard -> {DOCS}")
    print(f"GitHub Pages: {command_center['links']['github_pages']}")
    print(f"Netlify:      {command_center['links']['netlify']}")


if __name__ == "__main__":
    main()
