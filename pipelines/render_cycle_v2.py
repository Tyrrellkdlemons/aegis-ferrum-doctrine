#!/usr/bin/env python3
"""Render the v2 AEGIS episode from approved narration and generated scene art."""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import edge_tts
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
FFMPEG = Path(imageio_ffmpeg.get_ffmpeg_exe())
SLUG = "why_most_men_never_build_real_capability_v2"
VOICE_TEXT = ROOT / "assets" / "scripts" / "why_99_percent_men_never_dangerous_v2_voice.txt"
SCENE_DIR = ROOT / "assets" / "visuals" / "broll_v2"
VOICE_OUT = ROOT / "assets" / "voice" / f"{SLUG}_voice.mp3"
MUSIC = ROOT / "assets" / "voice" / "why_99_percent_men_never_dangerous_music.wav"
CAPTIONS = ROOT / "assets" / "scripts" / f"{SLUG}.srt"
FINAL_DIR = ROOT / "assets" / "final"
LONG_OUT = FINAL_DIR / f"{SLUG}_long.mp4"
SHORT_OUT = FINAL_DIR / f"{SLUG}_short.mp4"
REEL_OUT = FINAL_DIR / f"{SLUG}_reel.mp4"
TMP = ROOT / "assets" / "final" / ".v2_render"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def run(args: list[str | Path], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [str(x) for x in args]
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture,
        cwd=ROOT,
    )


def media_duration(path: Path) -> float:
    proc = run([FFMPEG, "-hide_banner", "-i", path, "-f", "null", "-"], capture=True)
    text = (proc.stderr or "") + (proc.stdout or "")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if not match:
        raise RuntimeError(f"Could not read duration for {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def fmt_srt(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def wrap_caption(text: str, width: int = 42) -> str:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if len(trial) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    if len(lines) > 2:
        lines = [" ".join(lines[:-1]), lines[-1]]
    return "\n".join(lines)


def make_srt(text: str, duration: float) -> None:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    weights = [max(12, len(s)) for s in sentences]
    usable = max(1.0, duration - 0.25)
    cursor = 0.0
    blocks: list[str] = []
    for idx, (sentence, weight) in enumerate(zip(sentences, weights), start=1):
        segment = usable * weight / sum(weights)
        end = min(duration, cursor + max(1.1, segment))
        blocks.append(
            f"{idx}\n{fmt_srt(cursor)} --> {fmt_srt(end)}\n{wrap_caption(sentence)}\n"
        )
        cursor = end
    atomic_write(CAPTIONS, "\n".join(blocks).rstrip() + "\n")


async def synthesize_voice(text: str) -> None:
    VOICE_OUT.parent.mkdir(parents=True, exist_ok=True)
    communicator = edge_tts.Communicate(
        text,
        voice="en-US-GuyNeural",
        rate="-6%",
        pitch="-5Hz",
        volume="+0%",
    )
    await communicator.save(str(VOICE_OUT))


def render_scene(index: int, image: Path, duration: float) -> Path:
    out = TMP / f"scene_{index:02d}.mp4"
    frames = max(1, math.ceil(duration * 24))
    direction = -1 if index % 2 else 1
    x_expr = "iw/2-(iw/zoom/2)"
    y_expr = "ih/2-(ih/zoom/2)"
    if direction < 0:
        x_expr = "max(0,iw/2-(iw/zoom/2)-on*0.04)"
    else:
        x_expr = "min(iw-iw/zoom,iw/2-(iw/zoom/2)+on*0.04)"
    vf = (
        "scale=2200:1238:force_original_aspect_ratio=increase,"
        "crop=2200:1238,"
        f"zoompan=z='min(zoom+0.00022,1.075)':x='{x_expr}':y='{y_expr}':"
        f"d={frames}:s=1920x1080:fps=24,"
        "format=yuv420p"
    )
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", image,
        "-vf", vf,
        "-t", f"{duration:.3f}",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-movflags", "+faststart", out,
    ])
    return out


def append_comms(lines: list[str]) -> None:
    path = ROOT / "comms_log.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# AEGIS Comms Log\n"
    atomic_write(path, existing.rstrip() + "\n\n" + "\n".join(lines) + "\n")


def update_task_board(final_status: str, details: str) -> None:
    path = ROOT / "task_board.json"
    if not path.exists():
        return
    board = json.loads(path.read_text(encoding="utf-8"))
    for task in board.get("tasks", []):
        if task.get("id") == "edit_001":
            task["status"] = final_status
            task["assigned"] = "SOVEREIGN/Editorius-v2"
            task["details"] = details
            task["updated_at"] = now_iso()
    board["updated_at"] = now_iso()
    atomic_write(path, json.dumps(board, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    if not VOICE_TEXT.exists():
        raise SystemExit(f"Missing narration: {VOICE_TEXT}")
    scenes = sorted(SCENE_DIR.glob("*.png"))
    if len(scenes) < 10:
        raise SystemExit(f"Need at least 10 approved scenes; found {len(scenes)}")
    if not MUSIC.exists():
        raise SystemExit(f"Missing original music bed: {MUSIC}")

    text = VOICE_TEXT.read_text(encoding="utf-8").strip()
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)

    print("[Vocem v2] Synthesizing approved narration...", flush=True)
    asyncio.run(synthesize_voice(text))
    duration = media_duration(VOICE_OUT)
    print(f"[Vocem v2] Narration duration: {duration:.2f}s", flush=True)
    make_srt(text, duration)

    per_scene = duration / len(scenes)
    print(f"[Editorius v2] Rendering {len(scenes)} scene motions...", flush=True)
    rendered: list[Path] = []
    with ThreadPoolExecutor(max_workers=min(4, os.cpu_count() or 4)) as pool:
        futures = {
            pool.submit(render_scene, idx, scene, per_scene): (idx, scene)
            for idx, scene in enumerate(scenes, start=1)
        }
        for future in as_completed(futures):
            idx, scene = futures[future]
            rendered.append(future.result())
            print(f"  scene {idx:02d}/{len(scenes)}: {scene.name}", flush=True)

    concat_list = TMP / "concat.txt"
    ordered = sorted(rendered)
    atomic_write(concat_list, "".join(f"file '{p.as_posix()}'\n" for p in ordered))
    visuals = TMP / "visuals.mp4"
    print("[Editorius v2] Concatenating scene motions...", flush=True)
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", visuals,
    ])

    caption_filter = (
        "subtitles=filename='assets/scripts/why_most_men_never_build_real_capability_v2.srt':"
        "force_style='FontName=Arial,FontSize=21,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&HAA000000,BackColour=&H88000000,BorderStyle=3,"
        "Outline=1,Shadow=0,Alignment=2,MarginV=58'"
    )
    audio_filter = (
        "[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[voice];"
        "[2:a]volume=0.09,afade=t=in:st=0:d=2[music];"
        "[voice][music]amix=inputs=2:duration=first:dropout_transition=2,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
    )
    print("[Editorius v2] Mixing, captioning, and encoding long form...", flush=True)
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", visuals, "-i", VOICE_OUT, "-stream_loop", "-1", "-i", MUSIC,
        "-vf", caption_filter,
        "-filter_complex", audio_filter,
        "-map", "0:v:0", "-map", "[aout]",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", LONG_OUT,
    ])

    short_filter = "crop=608:1080:(iw-608)/2:0,scale=1080:1920,format=yuv420p"
    print("[Editorius v2] Creating vertical short and reel...", flush=True)
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "0", "-i", LONG_OUT, "-t", "45",
        "-vf", short_filter,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", SHORT_OUT,
    ])
    shutil.copy2(SHORT_OUT, REEL_OUT)

    sizes = {p.name: p.stat().st_size for p in (LONG_OUT, SHORT_OUT, REEL_OUT)}
    if any(size <= 0 for size in sizes.values()):
        raise RuntimeError(f"Zero-byte output detected: {sizes}")
    update_task_board("review", f"v2 render produced; technical and visual QA required: {sizes}")
    append_comms([
        f"## {now_iso()} — Editorius v2 render produced",
        f"- Long: `{LONG_OUT.relative_to(ROOT)}` ({sizes[LONG_OUT.name]} bytes)",
        f"- Short: `{SHORT_OUT.relative_to(ROOT)}` ({sizes[SHORT_OUT.name]} bytes)",
        "- Status: review. Prometheus must run technical, audio, visual, rights, and disclosure checks before upload.",
    ])
    print(json.dumps({"duration": duration, "outputs": sizes}, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        update_task_board("rework", f"v2 render failed: {exc}")
        append_comms([
            f"## {now_iso()} — [PROMETHEUS] VETO: v2 render failed",
            f"- Error: `{type(exc).__name__}: {exc}`",
        ])
        raise
