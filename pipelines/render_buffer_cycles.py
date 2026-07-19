#!/usr/bin/env python3
"""Render buffered cycles 002-004 to publishable media (hook-first)."""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
from pathlib import Path

import edge_tts

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phoenix_render_and_buffer import (  # noqa: E402
    FUTURE,
    ambient,
    assemble,
    atomic_json,
    draw_hook_card,
    make_thumbnail,
    mix,
)

ROOT = Path(__file__).resolve().parents[1]

VOICES = {
    "ferrum-doctrine-002": """
Your ambition didn't die in a crisis. It bled out in habits you call harmless.

The kill is quiet. Snooze. Quick check. Late sugar. Open loops. Yes-man agreements you never meant. Soft habits win because they feel like rest while they steal your standards.

Ambition without a kill-list is cosplay. Name the three habits that own you. Write them. If you can't name them, they own you completely.

Replacement protocol. One hard morning block before the feed. One friction gate on the phone — app deleted or grayscale, no negotiation. One nightly shutdown where tomorrow's first move is already decided.

If you keep the soft habit, stop calling yourself ambitious. Call yourself entertained.

Comment KILL LIST with the habit you're executing this week. Subscribe for the next Ferrum Doctrine field manual.
""".strip(),
    "ferrum-doctrine-003": """
Speak first and you lose. Read first and you own the next five minutes.

Power maps beat small talk. Exits. Status. Anxiety. The unspoken rule. Who is performing, who has substance. Most men talk to soothe insecurity. Operators gather terrain.

Drill: ten-second scan before every meeting, gym, dinner, call. Then speak second — short, aimed, no apology padding.

Social intelligence is not niceness. It is accurate perception under pressure. Soft men perform warmth. Dangerous men deliver clarity.

Comment TERRAIN if you're running the ten-second scan for seven days. Subscribe. Ferrum Doctrine.
""".strip(),
    "ferrum-doctrine-004": """
If your attention is for rent, your life is already owned.

The feed is not entertainment. It is a weapons system aimed at your standards. Fortress rules: no phone in the first sixty minutes. One deep-work bunker. Notification famine.

Dopamine is not the enemy. Untrained dopamine is. Replace scroll with silence intervals and one hard promise kept daily.

Sovereignty starts where the algorithm loses access. Soft men negotiate with the feed. Operators cut the pipe.

Comment FORTRESS if you're locking the first hour tomorrow. Subscribe for the next field manual.
""".strip(),
}


async def tts(text: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    c = edge_tts.Communicate(text, voice="en-US-ChristopherNeural", rate="-6%", pitch="-4Hz")
    await c.save(str(out))


def main() -> None:
    for item in FUTURE:
        cid = item["id"]
        print(f"=== {cid} ===")
        voice = ROOT / "assets/voice" / f"{cid}_phoenix.mp3"
        music = ROOT / "assets/voice" / f"{cid}_music.wav"
        mixed = ROOT / "assets/voice" / f"{cid}_final.wav"
        asyncio.run(tts(VOICES[cid], voice))
        ambient(music, seconds=200)
        mix(voice, music, mixed)

        scene_dir = ROOT / "assets/visuals" / f"broll_{cid.replace('-', '_')}"
        scenes = []
        cards = [(item["hook"][:40], item["body_beats"][0][:100])]
        for i, b in enumerate(item["body_beats"]):
            cards.append((f"BEAT {i+1}", b[:110]))
        cards.append((item["cta"].split()[0:3] and " ".join(item["cta"].split()[:3]) or "CTA", item["cta"][:100]))
        for i, (h, s) in enumerate(cards[:12]):
            p = scene_dir / f"scene_{i+1:02d}.png"
            draw_hook_card(p, h.upper() if len(h) < 36 else h[:36].upper(), s, seed=300 + i)
            scenes.append(p)

        base = ROOT / "platforms/buffer" / cid / "youtube"
        make_thumbnail(base / "thumbnail_final.png", *item["thumb"])
        long_p = base / "final_long.mp4"
        short_p = base / "final_short.mp4"
        reel_tmp = base / "final_reel.mp4"
        assemble(mixed, scenes, long_p, short_p, reel_tmp)

        # mirror to platform-ready short packs
        ig = ROOT / "platforms/buffer" / cid / "instagram"
        tt = ROOT / "platforms/buffer" / cid / "tiktok"
        ig.mkdir(parents=True, exist_ok=True)
        tt.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reel_tmp, ig / "final_reel.mp4")
        shutil.copy2(short_p, tt / "final_tiktok.mp4")

        man = json.loads((base / "publish_manifest.json").read_text(encoding="utf-8"))
        man["status"] = "ready"
        man["file"] = "final_long.mp4"
        man["secondary_files"] = ["final_short.mp4"]
        man["audio_source"] = str(voice.relative_to(ROOT)).replace("\\", "/")
        atomic_json(base / "publish_manifest.json", man)
        (base / "VOICEOVER_PENDING.txt").unlink(missing_ok=True)
        (base / "final_long.mp4.PLACEHOLDER").unlink(missing_ok=True)
        print("  long bytes", long_p.stat().st_size)


if __name__ == "__main__":
    main()
