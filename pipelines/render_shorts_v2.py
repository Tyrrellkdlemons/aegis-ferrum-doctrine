#!/usr/bin/env python3
"""Render three caption-safe 9:16 shorts from the approved V2 adaptations."""

from __future__ import annotations

import asyncio
import math
import re
import shutil
import subprocess
from pathlib import Path

import edge_tts
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())
SCENES = ROOT / "assets" / "visuals" / "broll_v2"
MUSIC = ROOT / "assets" / "voice" / "why_99_percent_men_never_dangerous_music.wav"
OUT_DIR = ROOT / "assets" / "final" / "shorts_v2"
TMP = ROOT / "assets" / "final" / ".shorts_v2_render"

SPECS = [
    {
        "slug": "danger_is_not_rage",
        "title": "Danger Is Not Rage",
        "text": (
            "Danger is not rage. Rage removes options. Real capability is staying calm enough "
            "to see three constructive moves when everyone else sees one. Start with ten "
            "phone-free minutes today. When the urge to escape appears, name it. Do not obey it. "
            "That gap between impulse and action is where command begins."
        ),
        "scenes": ["03_silence_interval.png", "07_delayed_reaction_platform.png", "12_pause_before_reply.png"],
    },
    {
        "slug": "stoicism_is_not_numbness",
        "title": "Stoicism Is Not Numbness",
        "text": (
            "Stoicism is not feeling nothing. It is noticing anger, fear, and pride without "
            "letting them write your next move. When provoked, take one breath. Ask what the "
            "objective is: clarity, a boundary, a decision, or silence. Answer the objective, "
            "not the insult."
        ),
        "scenes": ["04_delayed_reply_meeting.png", "08_boundary_conversation.png", "05_controlled_exit.png"],
    },
    {
        "slug": "one_promise_rebuilds_self_trust",
        "title": "One Promise Rebuilds Self-Trust",
        "text": (
            "Stop designing heroic routines you cannot repeat. Pick one realistic promise for "
            "twenty-one days: a sleep window, a training block, or forty-five minutes of deep "
            "work before entertainment. Miss once? Record why, remove the obstacle, and resume. "
            "Discipline is evidence, not theater."
        ),
        "scenes": ["01_phone_down_journal.png", "09_deep_work.png", "06_disciplined_craft.png"],
    },
]


def run(args: list[str | Path], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(x) for x in args], check=True, text=True, capture_output=capture, cwd=ROOT
    )


def duration(path: Path) -> float:
    result = run([FFMPEG, "-hide_banner", "-i", path, "-f", "null", "-"], capture=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not determine duration for {path}")
    h, m, s = match.groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def ts(seconds: float) -> str:
    total = max(0, round(seconds * 1000))
    h, rem = divmod(total, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap(text: str, width: int = 23) -> str:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if current and len(" ".join(current + [word])) > width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def make_srt(text: str, total: float, path: Path) -> None:
    sentences = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    parts: list[str] = []
    for sentence in sentences:
        current: list[str] = []
        for word in sentence.split():
            if current and len(" ".join(current + [word])) > 38:
                parts.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            parts.append(" ".join(current))
    weights = [len(p) for p in parts]
    cursor = 0.0
    blocks = []
    for index, (part, weight) in enumerate(zip(parts, weights), start=1):
        end = min(total, cursor + total * weight / sum(weights))
        blocks.append(f"{index}\n{ts(cursor)} --> {ts(end)}\n{wrap(part)}\n")
        cursor = end
    path.write_text("\n".join(blocks), encoding="utf-8")


async def speak(text: str, out: Path) -> None:
    await edge_tts.Communicate(
        text, voice="en-US-GuyNeural", rate="-4%", pitch="-5Hz"
    ).save(str(out))


def render_scene(image: Path, out: Path, seconds: float, index: int) -> None:
    frames = math.ceil(seconds * 24)
    x = "iw/2-(iw/zoom/2)"
    y = "ih/2-(ih/zoom/2)"
    vf = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"zoompan=z='min(zoom+0.00025,1.06)':x='{x}':y='{y}':d={frames}:s=1080x1920:fps=24,"
        "format=yuv420p"
    )
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-i", image,
        "-vf", vf, "-t", f"{seconds:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "19", out,
    ])


def render_short(spec: dict[str, object], index: int) -> Path:
    slug = str(spec["slug"])
    work = TMP / slug
    work.mkdir(parents=True, exist_ok=True)
    voice = work / "voice.mp3"
    srt = work / "captions.srt"
    asyncio.run(speak(str(spec["text"]), voice))
    total = duration(voice)
    make_srt(str(spec["text"]), total, srt)

    rendered = []
    for scene_index, name in enumerate(spec["scenes"], start=1):
        out = work / f"scene_{scene_index:02d}.mp4"
        render_scene(SCENES / str(name), out, total / 3, scene_index)
        rendered.append(out)

    concat = work / "concat.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in rendered), encoding="utf-8")
    visuals = work / "visuals.mp4"
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", visuals])

    caption = (
        f"subtitles=filename='{srt.relative_to(ROOT).as_posix()}':"
        "force_style='FontName=Arial,FontSize=17,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&HAA000000,BackColour=&H90000000,BorderStyle=3,"
        "Outline=1,Shadow=0,Alignment=2,MarginL=40,MarginR=40,MarginV=58'"
    )
    audio = (
        "[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[voice];"
        "[2:a]volume=0.08[music];"
        "[voice][music]amix=inputs=2:duration=first:dropout_transition=2,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
    )
    out = OUT_DIR / f"{index:02d}_{slug}.mp4"
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", visuals, "-i", voice,
        "-stream_loop", "-1", "-i", MUSIC, "-vf", caption, "-filter_complex", audio,
        "-map", "0:v:0", "-map", "[aout]", "-t", f"{total:.3f}", "-c:v", "libx264",
        "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "160k", "-movflags",
        "+faststart", out,
    ])
    print(f"{out.name}: {total:.2f}s, {out.stat().st_size} bytes", flush=True)
    return out


def main() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [render_short(spec, index) for index, spec in enumerate(SPECS, start=1)]
    shutil.copy2(outputs[0], ROOT / "assets" / "final" / "why_most_men_never_build_real_capability_v2_short.mp4")
    shutil.copy2(outputs[0], ROOT / "assets" / "final" / "why_most_men_never_build_real_capability_v2_reel.mp4")


if __name__ == "__main__":
    main()
