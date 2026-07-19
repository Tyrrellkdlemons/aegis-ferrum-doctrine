#!/usr/bin/env python3
"""Phoenix Mode: organize platforms/ + copy media + write manifests."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def copy_to(src: Path, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.exists() and src.stat().st_size > 0:
        shutil.copy2(src, dest)
        return True
    dest.write_text(
        f"PLACEHOLDER — missing source: {src.name}\nExport settings TBD.\n",
        encoding="utf-8",
    )
    return False


def main() -> None:
    v2_long = ROOT / "assets/final/why_most_men_never_build_real_capability_v2_long.mp4"
    v1_long = ROOT / "assets/final/why_99_percent_men_never_dangerous_long.mp4"
    v2_short = ROOT / "assets/final/why_most_men_never_build_real_capability_v2_short.mp4"
    v1_short = ROOT / "assets/final/why_99_percent_men_never_dangerous_short.mp4"
    v2_reel = ROOT / "assets/final/why_most_men_never_build_real_capability_v2_reel.mp4"
    v1_reel = ROOT / "assets/final/why_99_percent_men_never_dangerous_reel.mp4"
    thumb = ROOT / "assets/visuals/thumbnails/thumbnail_final-v2.png"
    if not thumb.exists():
        thumb = ROOT / "assets/visuals/thumbnails/thumbnail_final.png"
    carousel = sorted((ROOT / "assets/visuals/carousel").glob("slide_*.png"))
    vertical = sorted((ROOT / "assets/visuals/vertical").glob("vert_*.png"))

    long_src = v2_long if v2_long.exists() and v2_long.stat().st_size > 1_000_000 else v1_long
    short_src = v2_short if v2_short.exists() and v2_short.stat().st_size > 1_000_000 else v1_short
    reel_src = v2_reel if v2_reel.exists() and v2_reel.stat().st_size > 1_000_000 else v1_reel

    cid = "ferrum-doctrine-001"
    title = "Why Most Men Will Never Be Dangerous — And Why That Should Terrify You | Ferrum Doctrine"
    desc = (
        "Most men volunteered to be soft — then lied about why.\n\n"
        "Danger is not rage. Danger is optionality under pressure.\n"
        "21-day field protocol inside. Comment OPERATIVE if you're done performing.\n\n"
        "TIMESTAMPS\n"
        "0:00 Soft by consent\n"
        "0:25 What dangerous actually means\n"
        "1:10 Four traps that keep you weak\n"
        "2:00 21-day drills\n"
        "Last: Pressure test\n\n"
        "Ferrum Doctrine — discipline without apology.\n"
    )
    tags = [
        "become dangerous", "stoic discipline", "masculine presence", "self improvement men",
        "mental toughness", "discipline protocol", "anti comfort", "ferrum doctrine",
        "stoicism for men", "personal responsibility", "mental fortress", "how to be dangerous",
        "dark psychology stoicism", "room control", "self mastery", "hard truths for men",
        "quit soft living", "21 day challenge", "operative mindset", "social dynamics men",
        "frame control", "cold stoic truth", "focus and discipline", "male self mastery",
        "power under pressure", "delayed gratification", "habit building men", "sovereignty",
    ]

    yt = ROOT / "platforms/youtube"
    copy_to(long_src, yt / "final_long.mp4")
    copy_to(short_src, yt / "final_short.mp4")
    copy_to(thumb, yt / "thumbnail_final.png")
    (yt / "WHAT_WHERE_WHEN.md").write_text(
        "# YouTube — WHAT / WHERE / WHEN\n\n"
        "- **WHAT:** Long-form + Short cut\n"
        "- **WHERE:** Ferrum Doctrine (UCh82kLGeSgdCd1VNEQsZ2pg) — tyrrellkdlemons@gmail.com\n"
        "- **WHEN:** 2026-07-19 12:00 UTC\n"
        "- **FILES:** final_long.mp4, final_short.mp4, thumbnail_final.png\n",
        encoding="utf-8",
    )
    (yt / "publish_manifest.json").write_text(
        json.dumps(
            {
                "platform": "youtube",
                "content_id": cid,
                "file": "final_long.mp4",
                "secondary_files": ["final_short.mp4"],
                "title": title,
                "description": desc,
                "tags": tags,
                "thumbnail": "thumbnail_final.png",
                "schedule": "2026-07-19T12:00:00Z",
                "status": "ready",
                "monetization": {
                    "midroll": True,
                    "affiliate_links": [],
                    "pinned_comment": "Comment OPERATIVE. Funnel URL pending — do not invent links.",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    ig = ROOT / "platforms/instagram"
    copy_to(reel_src, ig / "final_reel.mp4")
    for i, p in enumerate(carousel[:5], 1):
        copy_to(p, ig / f"carousel_{i:02d}.png")
    ig_caption = (
        "They sold you soft and called it balance.\n\n"
        "Danger ≠ rage.\nDanger = options under pressure.\n\n"
        "21-day protocol on YT.\nComment OPERATIVE.\n\n"
        "#discipline #stoicism #masculinity #selfimprovement #ferrumdoctrine #mindset #hardtruths\n"
    )
    (ig / "caption.txt").write_text(ig_caption, encoding="utf-8")
    (ig / "WHAT_WHERE_WHEN.md").write_text(
        "# Instagram — WHAT / WHERE / WHEN\n\n"
        "- **WHAT:** Reel + 5-slide carousel\n"
        "- **WHERE:** Brand IG\n"
        "- **WHEN:** 2026-07-19 17:00 UTC\n",
        encoding="utf-8",
    )
    (ig / "publish_manifest.json").write_text(
        json.dumps(
            {
                "platform": "instagram",
                "content_id": cid,
                "file": "final_reel.mp4",
                "secondary_files": [f"carousel_{i:02d}.png" for i in range(1, 6)],
                "title": "Soft is a choice. Danger is options.",
                "description": ig_caption,
                "tags": [
                    "discipline", "stoicism", "masculinity", "selfimprovement",
                    "ferrumdoctrine", "mindset", "hardtruths", "mentalstrength",
                ],
                "thumbnail": "carousel_01.png",
                "schedule": "2026-07-19T17:00:00Z",
                "status": "ready",
                "monetization": {"midroll": False, "affiliate_links": [], "pinned_comment": ""},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    tt = ROOT / "platforms/tiktok"
    copy_to(short_src, tt / "final_tiktok.mp4")
    tt_caption = (
        "Most men volunteered to be soft.\n\n"
        "Danger isn't screaming.\n"
        "It's still having three moves when everyone else has one.\n\n"
        "Comment OPERATIVE.\n\n"
        "#stoic #discipline #masculinity #mindset #ferrumdoctrine #selfimprovement\n"
    )
    (tt / "caption.txt").write_text(tt_caption, encoding="utf-8")
    (tt / "WHAT_WHERE_WHEN.md").write_text(
        "# TikTok — WHAT / WHERE / WHEN\n\n"
        "- **WHAT:** 9:16 short\n"
        "- **WHERE:** Brand TikTok\n"
        "- **WHEN:** 2026-07-19 18:30 UTC\n",
        encoding="utf-8",
    )
    (tt / "publish_manifest.json").write_text(
        json.dumps(
            {
                "platform": "tiktok",
                "content_id": cid,
                "file": "final_tiktok.mp4",
                "title": "Most men volunteered to be soft",
                "description": tt_caption,
                "tags": ["stoic", "discipline", "masculinity", "mindset", "ferrumdoctrine", "selfimprovement"],
                "thumbnail": None,
                "schedule": "2026-07-19T18:30:00Z",
                "status": "ready",
                "monetization": {"midroll": False, "affiliate_links": [], "pinned_comment": ""},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    x = ROOT / "platforms/x"
    x.mkdir(parents=True, exist_ok=True)
    thread = (
        "1/ Most men will never be dangerous. Not because the world is cruel — "
        "because they consent to soft living every day.\n\n"
        "2/ Soft culture sold comfort as virtue. Result: optional men. Easy to ignore. Easy to replace.\n\n"
        "3/ Danger ≠ rage. Rage is cheap. Danger = optionality under pressure.\n\n"
        "4/ You perform toughness online and outsource courage offline. That's cosplay.\n\n"
        "5/ Numbness isn't Stoicism. Accurate perception + deliberate action is.\n\n"
        "6/ 21-day stack: discomfort budget, silence, unsoftened truth, power map, "
        "delayed reply, one non-negotiable, controlled exit.\n\n"
        "7/ Pressure test: if heat arrives in one hour — options or excuses?\n\n"
        "8/ Comment OPERATIVE if you're done negotiating with your weakest self. "
        "Soft paths are crowded on purpose.\n"
    )
    (x / "thread.txt").write_text(thread, encoding="utf-8")
    for i, p in enumerate(vertical[:3], 1):
        copy_to(p, x / f"visual_{i:02d}.png")
    (x / "WHAT_WHERE_WHEN.md").write_text(
        "# X — WHAT / WHERE / WHEN\n\n"
        "- **WHAT:** 8-tweet thread + visuals\n"
        "- **WHERE:** Brand X\n"
        "- **WHEN:** 2026-07-19 13:00 UTC\n",
        encoding="utf-8",
    )
    (x / "publish_manifest.json").write_text(
        json.dumps(
            {
                "platform": "x",
                "content_id": cid,
                "file": "thread.txt",
                "secondary_files": ["visual_01.png", "visual_02.png", "visual_03.png"],
                "title": "Most men will never be dangerous — thread",
                "description": thread,
                "tags": ["stoicism", "discipline", "masculinity", "mindset"],
                "thumbnail": "visual_01.png",
                "schedule": "2026-07-19T13:00:00Z",
                "status": "ready",
                "monetization": {"midroll": False, "affiliate_links": [], "pinned_comment": ""},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    rd = ROOT / "platforms/reddit"
    rd.mkdir(parents=True, exist_ok=True)
    post = (
        "# Title\n"
        "Why most men stay soft (and the 21-day protocol I use to reverse it)\n\n"
        "# Body\n"
        "Soft living is usually consent, not destiny.\n\n"
        "Danger here means optionality under pressure — not violence.\n\n"
        "Protocol (21 days):\n"
        "1. Daily discomfort budget\n"
        "2. 10-min silence, no phone\n"
        "3. One unsoftened truth\n"
        "4. 10-second power map before speaking\n"
        "5. Delayed reply when provoked\n"
        "6. One non-negotiable\n"
        "7. Controlled exit from one diluting environment\n\n"
        "Comment which drill you're starting.\n"
    )
    (rd / "post.md").write_text(post, encoding="utf-8")
    (rd / "WHAT_WHERE_WHEN.md").write_text(
        "# Reddit — WHAT / WHERE / WHEN\n\n"
        "- **WHAT:** Value post\n"
        "- **WHERE:** r/getdisciplined (adapt for r/stoicism)\n"
        "- **WHEN:** 2026-07-20 15:00 UTC\n",
        encoding="utf-8",
    )
    (rd / "publish_manifest.json").write_text(
        json.dumps(
            {
                "platform": "reddit",
                "content_id": cid,
                "file": "post.md",
                "title": "Why most men stay soft (and the 21-day protocol I use to reverse it)",
                "description": post,
                "tags": ["discipline", "stoicism"],
                "thumbnail": None,
                "schedule": "2026-07-20T15:00:00Z",
                "status": "ready",
                "monetization": {"midroll": False, "affiliate_links": [], "pinned_comment": ""},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    sched = {
        "content_id": cid,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "posts": [
            {"platform": "youtube", "when": "2026-07-19T12:00:00Z", "file": "platforms/youtube/final_long.mp4", "status": "ready"},
            {"platform": "x", "when": "2026-07-19T13:00:00Z", "file": "platforms/x/thread.txt", "status": "ready"},
            {"platform": "instagram", "when": "2026-07-19T17:00:00Z", "file": "platforms/instagram/final_reel.mp4", "status": "ready"},
            {"platform": "tiktok", "when": "2026-07-19T18:30:00Z", "file": "platforms/tiktok/final_tiktok.mp4", "status": "ready"},
            {"platform": "reddit", "when": "2026-07-20T15:00:00Z", "file": "platforms/reddit/post.md", "status": "ready"},
        ],
    }
    (ROOT / "platforms/SCHEDULE.json").write_text(json.dumps(sched, indent=2) + "\n", encoding="utf-8")
    (ROOT / "platforms/README.md").write_text(
        "# Platforms — WHAT / WHERE / WHEN\n\n"
        "Each subfolder: media + `publish_manifest.json` + `WHAT_WHERE_WHEN.md`.\n\n"
        "Master clock: `SCHEDULE.json`\n\n"
        "Brand: **Ferrum Doctrine** · tyrrellkdlemons@gmail.com\n",
        encoding="utf-8",
    )
    print("OK long=", long_src.name, "bytes=", long_src.stat().st_size if long_src.exists() else 0)


if __name__ == "__main__":
    main()
