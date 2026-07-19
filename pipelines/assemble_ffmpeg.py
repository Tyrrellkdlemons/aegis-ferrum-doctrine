#!/usr/bin/env python3
"""Fast ffmpeg slideshow assembler for AEGIS long/short/reel outputs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
SLUG = "why_99_percent_men_never_dangerous"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = ROOT / "assets" / "voice" / "final_audio.wav"
BROLL = sorted((ROOT / "assets" / "visuals" / "broll").glob("scene_*.png"))
FINAL = ROOT / "assets" / "final"
FINAL.mkdir(parents=True, exist_ok=True)


def probe_duration(path: Path) -> float:
    # ffprobe may not ship with imageio ffmpeg binary; parse ffmpeg -i stderr
    r = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 90.0


def main() -> None:
    if not VOICE.exists() or not BROLL:
        raise SystemExit("Missing voice or broll")
    dur = probe_duration(VOICE)
    per = max(2.5, dur / len(BROLL))
    list_file = FINAL / "concat_list.txt"
    # Build stills-as-video segments then concat — simpler: one filter slideshow
    # Use zoompan Ken Burns per image via filter_complex is heavy; use concat demuxer of image loops.
    lines = []
    for img in BROLL:
        lines.append(f"file '{img.as_posix()}'")
        lines.append(f"duration {per:.3f}")
    lines.append(f"file '{BROLL[-1].as_posix()}'")  # concat quirk
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    long_path = FINAL / f"{SLUG}_long.mp4"
    short_path = FINAL / f"{SLUG}_short.mp4"
    reel_path = FINAL / f"{SLUG}_reel.mp4"

    # Long-form 16:9
    cmd_long = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-i", str(VOICE),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(long_path),
    ]
    print("Encoding long-form...")
    subprocess.run(cmd_long, check=True)

    # Short/Reel 9:16 first 45s
    cmd_short = [
        FFMPEG, "-y",
        "-i", str(long_path),
        "-t", "45",
        "-vf", "crop=ih*9/16:ih,scale=1080:1920,fps=24,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(short_path),
    ]
    print("Encoding short...")
    subprocess.run(cmd_short, check=True)
    print("Encoding reel...")
    subprocess.run(cmd_short[:-1] + [str(reel_path)], check=True)

    meta = {
        "long": str(long_path),
        "short": str(short_path),
        "reel": str(reel_path),
        "duration": dur,
        "long_bytes": long_path.stat().st_size,
        "short_bytes": short_path.stat().st_size,
    }
    (FINAL / f"{SLUG}_publish_packet.json").write_text(
        json.dumps({
            "channel_name": "Null Soft Protocol",
            "account_email": "tyrrellkdlemons@gmail.com",
            "title": "Why 99% of Men Will Never Be Dangerous (And How You Become the 1%) | Null Soft Protocol",
            "files": meta,
            "cta": "Comment OPERATIVE",
            "publish_blocked_reason": "Channel still hosts kids content (Truly For Children videos). Do not upload men's content until kids videos removed or a new brand channel is created.",
        }, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
