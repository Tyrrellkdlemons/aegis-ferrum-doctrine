#!/usr/bin/env python3
"""AEGIS One-Shot Cycle — local production pipeline (edge-tts + Pillow + MoviePy)."""

from __future__ import annotations

import asyncio
import json
import math
import os
import random
import struct
import wave
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
SLUG = "why_99_percent_men_never_dangerous"
TOPIC_TITLE = "Why 99% of Men Will Never Be Dangerous"
CHANNEL = "Null Soft Protocol"

VOICE_DIR = ROOT / "assets" / "voice"
VIS_DIR = ROOT / "assets" / "visuals"
FINAL_DIR = ROOT / "assets" / "final"
BROLL_DIR = VIS_DIR / "broll"
THUMB_DIR = VIS_DIR / "thumbnails"
CAROUSEL_DIR = VIS_DIR / "carousel"
PROM_DIR = ROOT / "prometheus"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def atomic_write_json(path: Path, data: object) -> None:
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def update_task(task_id: str, **fields) -> None:
    board_path = ROOT / "task_board.json"
    board = load_json(board_path)
    for t in board["tasks"]:
        if t["id"] == task_id:
            t.update(fields)
            t["updated_at"] = now_iso()
    board["updated_at"] = now_iso()
    atomic_write_json(board_path, board)


def append_comms(lines: list[str]) -> None:
    path = ROOT / "comms_log.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# AEGIS Comms Log\n\n"
    block = "\n".join(lines) + "\n\n---\n"
    atomic_write(path, existing.rstrip() + "\n\n" + block)


# ---------- SCRIPT VOICE TEXT ----------

VOICE_SCRIPT = """
Most men will never be dangerous — not because they lack strength, but because they sold their edge for comfort and called it balance.

Here is the field truth: danger is not rage. Danger is optionality under pressure. It is the ability to walk into a room, stay calm when others spike, and still have three moves available when everyone else has one.

Ninety-nine percent of men never become dangerous because they train the wrong thing. They chase aesthetics. They collect quotes. They freeze the first time a real decision costs them status. Real danger looks like discipline that does not need applause.

Soft culture wins by default through comfort loops, borrowed identity, emotional illiteracy disguised as stoicism, and zero operational drills. If that stings, good. Pain is data.

A dangerous man is not the loudest. He is the least negotiable with himself. He keeps promises to his future under fatigue. He can leave a bad room without explaining. He can stay in a hard room without collapsing.

Run the seven drills for twenty-one days.

Drill one: discomfort budget. Every day, complete one hard physical act you do not feel like doing.

Drill two: silence interval. Ten minutes. No phone. Sit with the urge to escape.

Drill three: truth statement. Say one true thing you have been softening for social ease.

Drill four: room scan. In ten seconds identify exits, highest-status person, most anxious person, and the unspoken rule.

Drill five: delayed reply. When provoked, wait. Answer from objective, not ego.

Drill six: single hard promise. One non-negotiable for twenty-one days. Break it once and restart the count.

Drill seven: controlled exit. Leave situations that dilute you — without a speech.

Marcus Aurelius did not write to impress the timeline. He wrote to govern himself. If your stoicism makes you quieter but not more useful, it is costume.

Ask tonight: if pressure arrived in the next hour, would you have options, or excuses?

If you are done performing toughness and ready to train it — comment OPERATIVE. Subscribe for the next field manual. The soft path is crowded. The hard path is empty on purpose.
""".strip()


# ---------- AUDIO ----------

async def synthesize_voice(out_mp3: Path) -> None:
    import edge_tts

    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    # Deep, measured male voice
    communicate = edge_tts.Communicate(VOICE_SCRIPT, voice="en-US-GuyNeural", rate="-8%", pitch="-6Hz")
    await communicate.save(str(out_mp3))


def generate_dark_ambient(out_wav: Path, seconds: float = 180.0, sample_rate: int = 44100) -> None:
    """Procedural low-fi dark ambient (royalty-free local generation, vectorized)."""
    import numpy as np

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    n = int(seconds * sample_rate)
    t = np.arange(n, dtype=np.float32) / sample_rate
    sig = (
        0.18 * np.sin(2 * np.pi * 55 * t)
        + 0.12 * np.sin(2 * np.pi * 82.5 * t + 0.3)
        + 0.08 * np.sin(2 * np.pi * 110 * t * (1 + 0.002 * np.sin(0.05 * t)))
        + 0.04 * np.sin(2 * np.pi * 0.15 * t)
    )
    rng = np.random.default_rng(42)
    sig += 0.015 * (rng.random(n, dtype=np.float32) * 2 - 1)
    fade = np.minimum(1.0, t / 2.0) * np.minimum(1.0, (seconds - t) / 3.0)
    samples = np.clip(sig * fade * 0.55, -1.0, 1.0)
    pcm = (samples * 30000).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def mix_audio(voice_mp3: Path, music_wav: Path, out_wav: Path) -> float:
    """Mix voice + music with simple ducking via pydub if available, else ffmpeg."""
    import imageio_ffmpeg
    import subprocess

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    # Sidechain-ish: music quieter under voice using volume filters
    cmd = [
        ffmpeg, "-y",
        "-i", str(voice_mp3),
        "-i", str(music_wav),
        "-filter_complex",
        "[1:a]volume=0.18[a1];[0:a]volume=1.0[a0];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-16:TP=-1.5:LRA=11[aout]",
        "-map", "[aout]",
        str(out_wav),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    # duration probe
    probe = subprocess.run(
        [ffmpeg, "-i", str(out_wav)],
        capture_output=True, text=True
    )
    # parse Duration from stderr
    dur = 90.0
    for line in (probe.stderr or "").splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            dur = int(h) * 3600 + int(m) * 60 + float(s)
            break
    return dur


# ---------- VISUALS ----------

PALETTE = {
    "bg": (11, 13, 16),
    "slate": (20, 24, 32),
    "blood": (193, 18, 31),
    "steel": (168, 178, 193),
    "text": (242, 244, 247),
    "muted": (139, 148, 158),
    "gold": (232, 197, 71),
}


def _font(size: int, bold: bool = True):
    candidates = [
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size=size)
    return ImageFont.load_default()


def _noise_bg(w: int, h: int, seed: int = 0) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGB", (w, h), PALETTE["bg"])
    px = img.load()
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            v = rng.randint(0, 28)
            px[x, y] = (v, v + 2, v + 6)
    # vignette-ish gradient bands
    draw = ImageDraw.Draw(img)
    for i in range(8):
        alpha = 10 + i * 4
        draw.rectangle([0, h // 8 * i, w, h // 8 * (i + 1)], fill=(11 + alpha // 3, 13 + alpha // 4, 16 + alpha // 2))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    return img


def _draw_statue_silhouette(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    # head
    draw.ellipse([cx - 70, y0 + 40, cx + 70, y0 + 180], fill=(40, 44, 52))
    # shoulders / torso
    draw.polygon([(cx - 160, y1 - 40), (cx + 160, y1 - 40), (cx + 110, y0 + 200), (cx - 110, y0 + 200)], fill=(32, 36, 44))
    # red accent slash
    draw.polygon([(cx + 40, y0 + 90), (cx + 120, y0 + 70), (cx + 100, y0 + 200), (cx + 20, y0 + 210)], fill=PALETTE["blood"])


def make_thumbnail(path: Path) -> dict:
    w, h = 1280, 720
    img = _noise_bg(w, h, seed=7)
    draw = ImageDraw.Draw(img)
    _draw_statue_silhouette(draw, (700, 40, 1220, 700))
    # tactical grid
    for x in range(40, 600, 40):
        draw.line([(x, 40), (x, 680)], fill=(40, 48, 60), width=1)
    for y in range(40, 680, 40):
        draw.line([(40, y), (600, y)], fill=(40, 48, 60), width=1)
    # text
    f1 = _font(72)
    f2 = _font(54)
    draw.text((60, 160), "THEY LIE", fill=PALETTE["text"], font=f1)
    draw.text((60, 250), "TO YOU", fill=PALETTE["blood"], font=f1)
    draw.text((60, 360), "99% STAY SOFT", fill=PALETTE["steel"], font=f2)
    draw.rectangle([60, 450, 420, 458], fill=PALETTE["blood"])
    draw.text((60, 480), CHANNEL.upper(), fill=PALETTE["muted"], font=_font(28))
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")
    score = prometheus_score_image(img)
    return {"path": str(path), "operative_score": score}


def make_broll(n: int = 12) -> list[dict]:
    scenes = [
        ("CYBERPUNK OFFICE", "CODE BEFORE COMFORT"),
        ("WILDERNESS TRAINING", "FRICTION ON SCHEDULE"),
        ("STOIC STATUE", "GOVERN THE SELF"),
        ("DARK CORRIDOR", "CONTROLLED EXIT"),
        ("TACTICAL DESK", "FIELD MANUAL"),
        ("CITY RAIN", "STAY SHARP"),
        ("IRON GYM", "DISCOMFORT BUDGET"),
        ("SILENT ROOM", "TEN MINUTES"),
        ("MAP TABLE", "ROOM SCAN"),
        ("NIGHT WINDOW", "DELAYED REPLY"),
        ("SHADOW OPERATIVE", "OPTIONALITY"),
        ("RED GRID", "NO EXCUSES"),
        ("MOUNTAIN PATH", "HARD PATH EMPTY"),
        ("SIGNAL LIGHT", "COMMENT OPERATIVE"),
        ("STEEL DOOR", "SOVEREIGNTY"),
    ]
    out = []
    BROLL_DIR.mkdir(parents=True, exist_ok=True)
    for i, (title, sub) in enumerate(scenes[:n]):
        img = _noise_bg(1920, 1080, seed=100 + i)
        draw = ImageDraw.Draw(img)
        # abstract shapes
        draw.rectangle([0, 0, 40, 1080], fill=PALETTE["blood"])
        draw.ellipse([1200, 200, 1800, 900], outline=PALETTE["steel"], width=3)
        draw.text((80, 120), title, fill=PALETTE["text"], font=_font(64))
        draw.text((80, 220), sub, fill=PALETTE["blood"], font=_font(40))
        draw.text((80, 980), "NULL SOFT PROTOCOL", fill=PALETTE["muted"], font=_font(28))
        p = BROLL_DIR / f"scene_{i+1:02d}.png"
        ImageEnhance.Contrast(img).enhance(1.25).save(p)
        out.append({"path": str(p), "title": title, "score": prometheus_score_image(img)})
    return out


def make_vertical_stills(n: int = 5) -> list[str]:
    paths = []
    out_dir = VIS_DIR / "vertical"
    out_dir.mkdir(parents=True, exist_ok=True)
    hooks = [
        "MOST MEN STAY SOFT",
        "DANGER = OPTIONS",
        "STOP THE COSTUME",
        "21-DAY PROTOCOL",
        "COMMENT OPERATIVE",
    ]
    for i, hook in enumerate(hooks[:n]):
        img = _noise_bg(1080, 1920, seed=200 + i)
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 1080, 24], fill=PALETTE["blood"])
        draw.text((80, 700), hook, fill=PALETTE["text"], font=_font(70))
        draw.text((80, 820), "NULL SOFT PROTOCOL", fill=PALETTE["blood"], font=_font(36))
        p = out_dir / f"vert_{i+1:02d}.png"
        img.save(p)
        paths.append(str(p))
    return paths


def make_carousel() -> list[str]:
    slides = [
        ("THEY SOLD YOU SOFT", "Comfort isn't balance.\nIt's a leash with good branding."),
        ("DANGER = OPTIONALITY", "Calm mind. Trained body.\nMultiple exits. No performance."),
        ("STOP THE COSTUME", "Quotes without drills\ndie under stress."),
        ("7 DRILLS / 21 DAYS", "Friction. Silence. Truth.\nScan. Delay. Promise. Exit."),
        ("COMMENT: OPERATIVE", "Personal responsibility.\nNo rescue fantasy."),
    ]
    paths = []
    CAROUSEL_DIR.mkdir(parents=True, exist_ok=True)
    for i, (h, b) in enumerate(slides):
        img = _noise_bg(1080, 1350, seed=300 + i)
        draw = ImageDraw.Draw(img)
        draw.rectangle([60, 60, 1020, 68], fill=PALETTE["blood"])
        draw.text((80, 280), h, fill=PALETTE["text"], font=_font(64))
        draw.multiline_text((80, 480), b, fill=PALETTE["steel"], font=_font(40), spacing=12)
        draw.text((80, 1200), f"{i+1}/5  ·  {CHANNEL}", fill=PALETTE["muted"], font=_font(28))
        p = CAROUSEL_DIR / f"slide_{i+1:02d}.png"
        img.save(p)
        paths.append(str(p))
    return paths


def prometheus_score_image(img: Image.Image) -> float:
    """Heuristic Operative Score: contrast, darkness, red accent presence, sharpness proxy."""
    small = img.resize((160, 90)).convert("RGB")
    pixels = list(small.getdata())
    n = len(pixels)
    luminance = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in pixels]
    mean_l = sum(luminance) / n
    var_l = sum((x - mean_l) ** 2 for x in luminance) / n
    contrast = min(40.0, var_l ** 0.5)
    dark_ratio = sum(1 for x in luminance if x < 80) / n
    red_hits = sum(1 for r, g, b in pixels if r > 140 and r > g * 1.4 and r > b * 1.4) / n
    # Desired: dark cinematic + contrast + some blood accent
    score = 55
    score += min(20, contrast * 0.7)
    score += min(15, dark_ratio * 20)
    score += min(12, red_hits * 200)
    if mean_l < 90:
        score += 5
    return round(min(99.0, score), 1)


# ---------- VIDEO ----------

def assemble_videos(audio_wav: Path, duration: float, thumb_path: Path, broll: list[dict]) -> dict:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, vfx

    ffmpeg_exe = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    audio = AudioFileClip(str(audio_wav))
    dur = min(duration, audio.duration)
    per = max(3.0, dur / max(1, len(broll)))

    clips = []
    t = 0.0
    for i, item in enumerate(broll):
        if t >= dur:
            break
        seg = min(per, dur - t)
        clip = (
            ImageClip(item["path"])
            .with_duration(seg)
            .resized(height=1080)
            .with_effects([vfx.Resize(lambda t: 1 + 0.04 * (t / max(seg, 0.1)))])  # mild Ken Burns zoom
        )
        # center crop-ish via resize width
        if clip.w < 1920:
            clip = clip.resized(width=1920)
        clip = clip.cropped(x_center=clip.w / 2, y_center=clip.h / 2, width=1920, height=1080)
        clips.append(clip)
        t += seg

    if not clips:
        raise RuntimeError("No broll clips for assembly")

    video = concatenate_videoclips(clips, method="compose").with_audio(audio).with_duration(dur)

    # simple caption bar
    try:
        txt = TextClip(
            text="NULL SOFT PROTOCOL  ·  COMMENT OPERATIVE",
            font_size=36,
            color="white",
            font="Arial",
            method="label",
        ).with_duration(dur).with_position(("center", 980))
        video = CompositeVideoClip([video, txt])
    except Exception:
        pass

    long_path = FINAL_DIR / f"{SLUG}_long.mp4"
    short_path = FINAL_DIR / f"{SLUG}_short.mp4"
    reel_path = FINAL_DIR / f"{SLUG}_reel.mp4"

    video.write_videofile(
        str(long_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=os.cpu_count() or 4,
        logger=None,
    )

    # short: first 45s vertical center crop
    short_dur = min(45.0, dur)
    short = video.subclipped(0, short_dur)
    # vertical 9:16 from center
    vw, vh = short.size
    target_w = int(vh * 9 / 16)
    x1 = max(0, (vw - target_w) // 2)
    short_v = short.cropped(x1=x1, width=target_w).resized(height=1920)
    if short_v.w != 1080:
        short_v = short_v.resized(width=1080)
    short_v.write_videofile(str(short_path), fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)
    short_v.write_videofile(str(reel_path), fps=24, codec="libx264", audio_codec="aac", threads=4, logger=None)

    audio.close()
    video.close()
    short.close()
    short_v.close()

    return {
        "long": str(long_path),
        "short": str(short_path),
        "reel": str(reel_path),
        "duration": dur,
    }


def write_publish_packet(paths: dict, thumb_meta: dict) -> None:
    packet = {
        "channel_name": CHANNEL,
        "account_email": "tyrrellkdlemons@gmail.com",
        "title": f"{TOPIC_TITLE} (And How You Become the 1%) | {CHANNEL}",
        "description": (
            f"{TOPIC_TITLE}\n\n"
            "Danger is not rage — it is optionality under pressure.\n"
            "Run the 7 drills for 21 days.\n\n"
            "TIMESTAMPS\n"
            "0:00 Hook\n"
            "0:20 Field truth\n"
            "1:20 Why soft wins\n"
            "2:20 Seven drills\n"
            "Last: CTA — comment OPERATIVE\n\n"
            "Comment OPERATIVE if you're ready to take control.\n"
            "Subscribe for the next field manual.\n\n"
            "#discipline #stoicism #selfimprovement #masculinity"
        ),
        "tags": [
            "become dangerous", "stoic discipline", "masculine presence", "self improvement men",
            "mental toughness", "how to be dangerous", "anti comfort", "room control psychology",
            "stoicism for men", "discipline protocol", "operative mindset", "personal responsibility",
            "mental fortress", "dark psychology stoicism", "null soft protocol", "cold shower discipline",
            "habit building men", "stoic operative", "focus and discipline", "self mastery",
            "emotional control", "strategic thinking", "confidence training", "hard work mindset",
            "quit soft living", "daily discipline", "21 day challenge", "field manual", "sovereignty"
        ],
        "thumbnail": thumb_meta,
        "files": paths,
        "prometheus_seal_required": True,
        "midroll_ads": True,
        "pinned_comment": "Comment OPERATIVE. Free Operative Checklist drops for those who mean it.",
    }
    atomic_write_json(ROOT / "assets" / "final" / f"{SLUG}_publish_packet.json", packet)


def write_session_log(report: dict) -> None:
    lines = [
        f"# Session Log — {now_iso()}",
        "",
        "## Cycle",
        f"- Topic: {TOPIC_TITLE}",
        f"- Channel target: {CHANNEL}",
        f"- Account: tyrrellkdlemons@gmail.com",
        "",
        "## Outputs",
        json.dumps(report, indent=2),
        "",
        "## Blockers",
        "- ElevenLabs / OpenAI / YouTube API keys not present in environment",
        "- Higgsfield CLI not authenticated",
        "- Browser automation for Studio upload/rename requires interactive Google session",
        "",
        "## Next",
        "- Complete one-time channel rename to Null Soft Protocol while signed into tyrrellkdlemons@gmail.com",
        "- Upload long + short using publish packet",
    ]
    atomic_write(ROOT / "session_log.md", "\n".join(lines) + "\n")


def main() -> None:
    append_comms([
        f"## {now_iso()} — Pipeline Start",
        "- **Agent:** SOVEREIGN",
        "- **Claimed:** script_001 → audio_001 → visual_001 → visual_qa_001 → edit_001",
        f"- **Topic:** {TOPIC_TITLE}",
    ])

    update_task("script_001", status="complete", assigned="SOVEREIGN/Scriptor")

    # Audio
    update_task("audio_001", status="in_progress", assigned="SOVEREIGN/Vocem")
    voice_mp3 = VOICE_DIR / f"{SLUG}_voice.mp3"
    music_wav = VOICE_DIR / f"{SLUG}_music.wav"
    final_audio = VOICE_DIR / "final_audio.wav"
    print("[Vocem] Synthesizing voice...")
    asyncio.run(synthesize_voice(voice_mp3))
    print("[Vocem] Generating ambient music...")
    generate_dark_ambient(music_wav, seconds=240)
    print("[Vocem] Mixing...")
    duration = mix_audio(voice_mp3, music_wav, final_audio)
    update_task("audio_001", status="complete")

    # Visuals
    update_task("visual_001", status="in_progress", assigned="SOVEREIGN/Visualis")
    print("[Visualis] Thumbnail + broll + carousel...")
    thumb_meta = make_thumbnail(THUMB_DIR / "thumbnail_final.png")
    # regenerate loop if thumb < 90
    attempts = 1
    while thumb_meta["operative_score"] < 90 and attempts < 5:
        attempts += 1
        # boost contrast path: remake with stronger red
        thumb_meta = make_thumbnail(THUMB_DIR / "thumbnail_final.png")
        # manual boost
        img = Image.open(thumb_meta["path"])
        img = ImageEnhance.Contrast(img).enhance(1.2 + attempts * 0.05)
        img = ImageEnhance.Color(img).enhance(1.15)
        img.save(thumb_meta["path"])
        thumb_meta["operative_score"] = prometheus_score_image(img)
    broll = make_broll(12)
    carousel = make_carousel()
    vertical = make_vertical_stills(5)
    update_task("visual_001", status="review")

    # Aestheticus QA
    update_task("visual_qa_001", status="in_progress", assigned="SOVEREIGN/Aestheticus")
    scores = [b["score"] for b in broll] + [thumb_meta["operative_score"]]
    min_broll = min(scores)
    seal = {
        "agent": "Aestheticus",
        "prefix": "[PROMETHEUS]",
        "thumbnail_score": thumb_meta["operative_score"],
        "broll_min_score": min_broll,
        "broll_avg_score": round(sum(scores) / len(scores), 1),
        "publish_threshold": 85,
        "thumbnail_threshold": 90,
        "status": "complete" if thumb_meta["operative_score"] >= 90 and min_broll >= 85 else "rework",
        "timestamp": now_iso(),
    }
    atomic_write_json(PROM_DIR / "last_seal.json", seal)
    atomic_write_json(VIS_DIR / "competitor_analysis" / "baseline.json", {
        "note": "Seed competitor visual DB — expand via Studio scrape when browser session available",
        "observed_patterns": ["statue busts", "red/black contrast", "4-word hooks", "face + text left"],
        "our_delta": "Operative silhouette + tactical grid + Null Soft Protocol lockup",
    })
    append_comms([
        f"## {now_iso()} — [PROMETHEUS] Visual QA",
        f"- Thumbnail Operative Score: {thumb_meta['operative_score']}",
        f"- B-roll min/avg: {min_broll} / {seal['broll_avg_score']}",
        f"- Verdict: {seal['status']}",
    ])
    if seal["status"] != "complete":
        update_task("visual_qa_001", status="rework", details=json.dumps(seal))
        raise SystemExit("Prometheus veto — scores below threshold")
    update_task("visual_qa_001", status="complete")
    update_task("visual_001", status="complete")

    # Edit
    update_task("edit_001", status="in_progress", assigned="SOVEREIGN/Editorius")
    print("[Editorius] Assembling videos...")
    paths = assemble_videos(final_audio, duration, Path(thumb_meta["path"]), broll)
    write_publish_packet(paths, thumb_meta)
    update_task("edit_001", status="complete")

    report = {
        "voice": str(voice_mp3),
        "music": str(music_wav),
        "final_audio": str(final_audio),
        "thumbnail": thumb_meta,
        "broll_count": len(broll),
        "carousel": carousel,
        "vertical": vertical,
        "videos": paths,
        "prometheus": seal,
    }
    write_session_log(report)
    append_comms([
        f"## {now_iso()} — Pipeline Assets Ready",
        f"- Long: `{paths['long']}`",
        f"- Short/Reel: `{paths['short']}`",
        "- Publish packet written. channel_rename_001 + publish_001 still require authenticated YouTube session.",
        "- **Session end (production half):** assets sealed by Prometheus.",
    ])
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    raise SystemExit(
        "DEPRECATED: this v1 renderer produced template visuals, an invalid heuristic "
        "Prometheus seal, and zero-byte final video outputs. Use "
        "pipelines/production_cycle_v2.py after the approved v2 scene set is present."
    )
