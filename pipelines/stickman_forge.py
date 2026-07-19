#!/usr/bin/env python3
"""
STICKMAN FORGE — Ferrum Doctrine vertical combat-lesson shorts.
PIL stick figures + edge-tts + ffmpeg. Output 1080x1920.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FPS = 24

LESSONS = [
    {
        "id": "lesson_01",
        "title": "Comfort Is a Cage",
        "hook": "Your comfort is not rest. It is a cage you decorate.",
        "body": "Every easy hit — scroll, snack, snooze — trains you to flinch from friction. Soft men call it balance. Operators call it surrender. You do not escape a cage by polishing the bars.",
        "demand": "Cut one comfort ritual tomorrow morning. Miss it and you chose the cage. Decide.",
        "combat": "cage",
    },
    {
        "id": "lesson_02",
        "title": "Respect Is Earned Under Pressure",
        "hook": "Most men die without ever being respected. Here's why.",
        "body": "Respect is not requested. It is the residue of kept standards when it costs you. Perform toughness online and fold offline — and you become optional. Pressure is the only exam that counts.",
        "demand": "Keep one hard promise for seven days. Break it and restart. Or stay invisible. Decide.",
        "combat": "duel_win",
    },
    {
        "id": "lesson_03",
        "title": "Your Phone Owns You",
        "hook": "If your attention is for rent, your life is already owned.",
        "body": "The feed is not entertainment. It is a weapons system aimed at your standards. Soft men negotiate with the algorithm. Operators cut the pipe. Sovereignty starts where the phone loses access.",
        "demand": "First sixty minutes tomorrow — no phone. Fail and you stay leased. Decide.",
        "combat": "phone_smash",
    },
    {
        "id": "lesson_04",
        "title": "Cheap Pleasure Steals Your Frame",
        "hook": "You cannot lead a room when your nervous system is rented by cheap hits.",
        "body": "Porn, endless games, micro-rewards — they do not relax you. They flatten your hunger. A man with a rented reward system cannot hold frame, finish hard work, or tolerate boredom. That is not freedom. That is sedation.",
        "demand": "Thirty days without your cheapest hit. Or stay sedated. Decide.",
        "combat": "shadow_defeat",
    },
    {
        "id": "lesson_05",
        "title": "Speak Second",
        "hook": "Speak first and you lose. Read first and you own the next five minutes.",
        "body": "Soft men talk to soothe insecurity. Operators gather terrain — exits, status, anxiety, unspoken rule. Ten seconds of silence beats ten minutes of noise. Social power is perception under pressure, not charm.",
        "demand": "Run a ten-second room scan before you speak — seven days. Or stay loud and weak. Decide.",
        "combat": "stance",
    },
    {
        "id": "lesson_06",
        "title": "Soft Habits Bleed Ambition",
        "hook": "Your ambition did not die in a crisis. It bled out in habits you call harmless.",
        "body": "Snooze. Quick check. Open loops. Yes-man agreements. Soft habits win because they feel like rest while they steal standards. Ambition without a kill-list is cosplay.",
        "demand": "Name three soft habits tonight. Kill one this week. Or stay entertained. Decide.",
        "combat": "bleed",
    },
    {
        "id": "lesson_07",
        "title": "Pain Is Tuition",
        "hook": "If growth never hurts, you are not growing. You are rearranging comfort.",
        "body": "Anti-fragility is built by voluntary stress on schedule — lift, cold, hard truth, deep work. Soft men wait to feel ready. Operators schedule readiness out of existence. Pain paid in advance is cheaper than pain collected by life.",
        "demand": "One discomfort budget daily for twenty-one days. Skip and you skipped the tuition. Decide.",
        "combat": "train",
    },
    {
        "id": "lesson_08",
        "title": "Nobody Is Coming",
        "hook": "Nobody is coming to make you formidable.",
        "body": "Not the algorithm. Not a mentor who cares more than you do. Not a relationship that will install your spine. The soft machine is already running. You either build a counter-protocol or you become inventory.",
        "demand": "Write your counter-protocol tonight — three rules. Or stay inventory. Decide.",
        "combat": "alone",
    },
    {
        "id": "lesson_09",
        "title": "Options Beat Excuses",
        "hook": "When pressure hits, soft men produce stories. Dangerous men produce options.",
        "body": "Options come from training: body, silence, truth, delayed reply, one non-negotiable. Excuses come from performance. Danger is not rage. Danger is optionality under pressure.",
        "demand": "Pressure-test tonight: money, status, body — options or excuses? Build one option tomorrow. Decide.",
        "combat": "fork",
    },
    {
        "id": "lesson_10",
        "title": "One Non-Negotiable",
        "hook": "If everything is flexible, you are not disciplined. You are negotiable.",
        "body": "Self-trust is the weapon. One non-negotiable — sleep, training, or deep work — kept when nobody watches. Break it and restart the count. Without self-trust every system is costume.",
        "demand": "Pick one non-negotiable before midnight. Keep it twenty-one days. Or stay optional. Decide.",
        "combat": "oath",
    },
]


def font(size: int):
    for c in [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]:
        if os.path.exists(c):
            return ImageFont.truetype(c, size=size)
    return ImageFont.load_default()


def draw_stick(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    scale: float = 1.0,
    color=(255, 255, 255),
    pose: str = "idle",
    accent: bool = False,
) -> None:
    """cy = hip center. pose drives limb angles."""
    s = scale
    head_r = int(28 * s)
    # poses: hip, shoulder offset, arm angles, leg angles (degrees from down)
    poses = {
        "idle": (0, 0, -20, 20, -8, 8),
        "guard": (0, -10, -110, 40, -15, 20),
        "strike": (-5, -20, -150, 60, -25, 35),
        "advance": (10, -5, -90, 30, -40, 25),
        "submit": (0, 40, 40, 50, 35, -35),
        "train": (0, -15, -160, -40, -20, 30),
        "point": (0, -10, -20, -170, -10, 15),
        "fall": (40, 60, 80, 100, 70, 50),
    }
    hip_dx, sh_dy, la, ra, ll, rl = poses.get(pose, poses["idle"])
    hip = (cx + int(hip_dx * s), cy)
    shoulder = (cx + int(hip_dx * s), cy - int(90 * s) + int(sh_dy * s))
    head = (shoulder[0], shoulder[1] - head_r - int(8 * s))
    w = max(3, int(4 * s))

    def limb(origin, angle_deg, length):
        rad = math.radians(angle_deg)
        # 180 = down
        a = math.radians(90) + rad  # convert: 0=down in our convention using angle from vertical
        # Use: angle 0 = straight down
        x2 = origin[0] + int(length * math.sin(math.radians(angle_deg)))
        y2 = origin[1] + int(length * math.cos(math.radians(angle_deg)))
        return x2, y2

    # Better limb: angle 0 = down, positive = clockwise-ish to the right
    def end(ox, oy, ang, length):
        # ang degrees from downward, positive to viewer's right
        rad = math.radians(ang)
        return ox + int(length * math.sin(rad)), oy + int(length * math.cos(rad))

    # torso
    draw.line([hip, shoulder], fill=color, width=w)
    draw.ellipse(
        [head[0] - head_r, head[1] - head_r, head[0] + head_r, head[1] + head_r],
        outline=color,
        width=w,
    )
    # arms from shoulder
    arm_len = int(70 * s)
    leg_len = int(85 * s)
    l_hand = end(shoulder[0], shoulder[1], la, arm_len)
    r_hand = end(shoulder[0], shoulder[1], ra, arm_len)
    draw.line([shoulder, l_hand], fill=color, width=w)
    draw.line([shoulder, r_hand], fill=color, width=w)
    # legs
    l_foot = end(hip[0], hip[1], ll, leg_len)
    r_foot = end(hip[0], hip[1], rl, leg_len)
    draw.line([hip, l_foot], fill=color, width=w)
    draw.line([hip, r_foot], fill=color, width=w)
    # red belt / tie for operative
    if accent:
        bw = int(36 * s)
        draw.rectangle(
            [hip[0] - bw, hip[1] - int(6 * s), hip[0] + bw, hip[1] + int(4 * s)],
            fill=(193, 18, 31),
        )
        # short red drop
        draw.line(
            [hip[0], hip[1], hip[0] + int(10 * s), hip[1] + int(28 * s)],
            fill=(193, 18, 31),
            width=max(2, w - 1),
        )


def scene_bg() -> Image.Image:
    img = Image.new("RGB", (W, H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    # faint tactical grid
    for x in range(0, W, 60):
        draw.line([(x, 0), (x, H)], fill=(18, 18, 18), width=1)
    for y in range(0, H, 60):
        draw.line([(0, y), (W, y)], fill=(18, 18, 18), width=1)
    # watermark
    draw.text((40, H - 70), "FERRUM DOCTRINE", fill=(80, 80, 80), font=font(28))
    return img


def wrap(text: str, max_chars: int = 28) -> str:
    words = text.split()
    lines, cur = [], []
    for w in words:
        trial = (" ".join(cur + [w]))
        if len(trial) <= max_chars:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return "\n".join(lines)


def render_combat_frame(combat: str, phase: int, overlay: str, overlay_color=(193, 18, 31)) -> Image.Image:
    img = scene_bg()
    draw = ImageDraw.Draw(img)
    # ground line
    draw.line([(80, 1400), (1000, 1400)], fill=(60, 60, 60), width=3)

    op_x, en_x = 350, 750
    hip_y = 1180

    if combat == "cage":
        # bars
        for x in range(200, 900, 70):
            draw.line([(x, 700), (x, 1400)], fill=(50, 50, 50), width=4)
        poses = ["submit", "idle", "guard", "strike"]
        draw_stick(draw, 540, hip_y, 1.35, (255, 255, 255), poses[phase % 4], accent=True)
    elif combat == "duel_win":
        seq_op = ["guard", "advance", "strike", "point"]
        seq_en = ["guard", "guard", "fall", "fall"]
        draw_stick(draw, op_x, hip_y, 1.3, (255, 255, 255), seq_op[phase % 4], accent=True)
        draw_stick(draw, en_x, hip_y + (80 if seq_en[phase % 4] == "fall" else 0), 1.2, (90, 90, 90), seq_en[phase % 4])
    elif combat == "phone_smash":
        draw_stick(draw, 500, hip_y, 1.35, (255, 255, 255), ["idle", "guard", "strike", "point"][phase % 4], accent=True)
        # phone rect
        px, py = 720, 900 - phase * 40
        draw.rectangle([px, py, px + 70, py + 120], outline=(120, 120, 120), width=4)
        if phase >= 2:
            draw.line([px, py, px + 70, py + 120], fill=(193, 18, 31), width=4)
    elif combat == "shadow_defeat":
        draw_stick(draw, op_x, hip_y, 1.3, (255, 255, 255), ["guard", "strike", "advance", "point"][phase % 4], accent=True)
        draw_stick(draw, en_x, hip_y, 1.25, (70, 70, 70), ["advance", "fall", "fall", "submit"][phase % 4])
    elif combat == "stance":
        draw_stick(draw, 540, hip_y, 1.4, (255, 255, 255), ["idle", "guard", "point", "guard"][phase % 4], accent=True)
        # scan arcs
        draw.arc([200, 600, 880, 1300], 200, 340, fill=(193, 18, 31), width=3)
    elif combat == "bleed":
        draw_stick(draw, 540, hip_y, 1.3, (255, 255, 255), ["submit", "idle", "guard", "advance"][phase % 4], accent=True)
        for i in range(phase + 1):
            draw.ellipse([200 + i * 80, 1450, 230 + i * 80, 1480], fill=(120, 20, 28))
    elif combat == "train":
        draw_stick(draw, 540, hip_y, 1.35, (255, 255, 255), ["train", "strike", "train", "guard"][phase % 4], accent=True)
    elif combat == "alone":
        draw_stick(draw, 540, hip_y, 1.4, (255, 255, 255), ["idle", "point", "guard", "point"][phase % 4], accent=True)
    elif combat == "fork":
        draw_stick(draw, 400, hip_y, 1.25, (255, 255, 255), ["point", "advance", "strike", "point"][phase % 4], accent=True)
        draw_stick(draw, 720, hip_y, 1.15, (80, 80, 80), ["submit", "fall", "submit", "fall"][phase % 4])
        draw.text((280, 1500), "OPTIONS", fill=(193, 18, 31), font=font(36))
        draw.text((680, 1500), "EXCUSES", fill=(90, 90, 90), font=font(36))
    elif combat == "oath":
        draw_stick(draw, 540, hip_y, 1.4, (255, 255, 255), ["guard", "point", "idle", "point"][phase % 4], accent=True)
        draw.rectangle([300, 560, 780, 620], outline=(193, 18, 31), width=3)
        draw.text((340, 570), "NON-NEGOTIABLE", fill=(193, 18, 31), font=font(36))
    else:
        draw_stick(draw, 540, hip_y, 1.3, (255, 255, 255), "guard", accent=True)

    # overlay text
    if overlay:
        block = wrap(overlay, 26)
        # shadow box
        ty = 220
        draw.rectangle([60, ty - 30, 1020, ty + 40 + 48 * block.count("\n")], fill=(0, 0, 0))
        draw.multiline_text((80, ty), block, fill=overlay_color, font=font(52), spacing=8, align="left")

    # top brand bar
    draw.rectangle([0, 0, W, 12], fill=(193, 18, 31))
    return img


def voice_script(lesson: dict) -> str:
    return (
        f"{lesson['hook']} {lesson['body']} {lesson['demand']} Ferrum."
    )


async def tts(text: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    c = edge_tts.Communicate(text, voice="en-US-ChristopherNeural", rate="-4%", pitch="-5Hz")
    await c.save(str(out))


def probe_duration(path: Path) -> float:
    r = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 55.0


def build_video(lesson: dict, voice: Path, out_mp4: Path) -> None:
    dur = probe_duration(voice)
    # aim 45-60s; pad/trim via -shortest with generated frames covering dur
    n_phases = 4
    # overlays by time thirds
    overlays = [
        (0.00, 0.12, lesson["hook"], (255, 255, 255)),
        (0.12, 0.72, lesson["body"].split(". ")[0] + ".", (193, 18, 31)),
        (0.72, 0.92, lesson["demand"].split(".")[0] + ".", (255, 255, 255)),
        (0.92, 1.01, "FERRUM", (193, 18, 31)),
    ]
    frame_dir = out_mp4.parent / f".frames_{lesson['id']}"
    if frame_dir.exists():
        for p in frame_dir.glob("*.png"):
            p.unlink()
    frame_dir.mkdir(parents=True, exist_ok=True)

    total_frames = max(int(dur * FPS), FPS * 45)
    paths = []
    for i in range(total_frames):
        t = i / total_frames
        phase = min(3, int(t * n_phases))
        overlay, color = "", (193, 18, 31)
        for a, b, text, col in overlays:
            if a <= t < b:
                overlay, color = text, col
                break
        img = render_combat_frame(lesson["combat"], phase, overlay, color)
        fp = frame_dir / f"f_{i:05d}.png"
        # write every frame is heavy — write every 2nd and duplicate? Better: write key segments
        img.save(fp)
        paths.append(fp)
        if i % 48 == 0:
            print(f"  {lesson['id']} frame {i}/{total_frames}")

    # ffmpeg from image sequence
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    pattern = str(frame_dir / "f_%05d.png")
    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", pattern,
        "-i", str(voice),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    # cleanup frames to save disk
    for p in frame_dir.glob("*.png"):
        p.unlink()
    try:
        frame_dir.rmdir()
    except OSError:
        pass


def write_script(lesson: dict) -> Path:
    d = ROOT / "content_core" / "stickman_lessons" / "scripts"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{lesson['id']}.md"
    p.write_text(
        f"""# {lesson['id'].upper()} — {lesson['title']}

**Series:** Ferrum Doctrine Stickman Combat Lessons  
**Length:** ~55s · Vertical 9:16  
**Brand sting:** Ferrum

## HOOK (0–3s)
{lesson['hook']}

## LESSON (3–45s)
{lesson['body']}

## DEMAND (45–55s)
{lesson['demand']}

## STING
Ferrum.

## VOICEOVER (full)
{voice_script(lesson)}
""",
        encoding="utf-8",
    )
    return p


def write_manifests(lesson: dict, video_rel: str, index: int, day0: datetime) -> None:
    when = day0 + timedelta(hours=10 + index * 3)
    title = f"{lesson['title']} | Ferrum Doctrine Stickman"
    desc = (
        f"{lesson['hook']}\n\n"
        f"{lesson['demand']}\n\n"
        "Ferrum Doctrine — stickman combat lessons for men who want standards.\n\n"
        "#FerrumDoctrine #Discipline #Stickman #Masculinity #SelfMastery #HardTruths #Mindset\n"
    )
    tags = [
        "ferrum doctrine", "stickman", "discipline", "self mastery", "hard truths for men",
        "masculinity", "stoicism", "frame control", "anti comfort", "short lesson",
    ]
    for plat, folder in [
        ("youtube", ROOT / "platforms" / "youtube_shorts" / lesson["id"]),
        ("instagram", ROOT / "platforms" / "instagram_reels" / lesson["id"]),
        ("tiktok", ROOT / "platforms" / "tiktok" / "stickman" / lesson["id"]),
    ]:
        folder.mkdir(parents=True, exist_ok=True)
        # copy note — actual file lives in assets/final/stickman; manifest points there
        man = {
            "platform": plat if plat != "youtube" else "youtube_shorts",
            "content_id": f"stickman-{lesson['id']}",
            "series": "Ferrum Doctrine Stickman Combat Lessons",
            "file": video_rel,
            "title": title,
            "description": desc,
            "tags": tags,
            "thumbnail": None,
            "schedule": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "review",
            "pinned_comment": "You either do the demand or stay weak. Decide. Full channel: The Tyrrell Codex / Ferrum Doctrine.",
            "monetization": {"midroll": False, "affiliate_links": [], "pinned_comment": "Decide. Or stay weak."},
        }
        (folder / "publish_manifest.json").write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
        (folder / "WHAT_WHERE_WHEN.md").write_text(
            f"# {lesson['title']}\n\n- WHAT: Stickman lesson MP4\n"
            f"- WHERE: {plat}\n- WHEN: {man['schedule']}\n"
            f"- FILE: {video_rel}\n",
            encoding="utf-8",
        )


def process_one(lesson: dict, day0: datetime) -> dict:
    print(f"=== {lesson['id']} {lesson['title']} ===")
    write_script(lesson)
    voice = ROOT / "assets" / "voice" / "stickman" / f"{lesson['id']}_voice.mp3"
    asyncio.run(tts(voice_script(lesson), voice))
    out = ROOT / "assets" / "final" / "stickman" / f"{lesson['id']}.mp4"
    # Faster path: fewer unique frames — render 4 pose frames and hold with concat durations
    build_video_fast(lesson, voice, out)
    rel = f"assets/final/stickman/{lesson['id']}.mp4"
    write_manifests(lesson, rel, int(lesson["id"].split("_")[1]) - 1, day0)
    return {"id": lesson["id"], "title": lesson["title"], "file": rel, "bytes": out.stat().st_size if out.exists() else 0}


def build_video_fast(lesson: dict, voice: Path, out_mp4: Path) -> None:
    """4 combat phases as held clips — sharp cuts, briefing style (not cartoon bounce)."""
    dur = probe_duration(voice)
    seg = max(dur / 4.0, 3.0)
    frame_dir = out_mp4.parent / f".kf_{lesson['id']}"
    frame_dir.mkdir(parents=True, exist_ok=True)
    overlays = [
        lesson["hook"],
        lesson["body"].split(". ")[0] + ".",
        lesson["demand"].split(".")[0] + ".",
        "FERRUM",
    ]
    colors = [(255, 255, 255), (193, 18, 31), (255, 255, 255), (193, 18, 31)]
    list_file = frame_dir / "concat.txt"
    lines = []
    for i in range(4):
        img = render_combat_frame(lesson["combat"], i, overlays[i], colors[i])
        fp = frame_dir / f"k_{i}.png"
        img.save(fp)
        lines.append(f"file '{fp.resolve().as_posix()}'")
        lines.append(f"duration {seg:.3f}")
    lines.append(f"file '{(frame_dir / 'k_3.png').resolve().as_posix()}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-i", str(voice),
        "-vf", "scale=1080:1920,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    # cleanup
    for p in frame_dir.glob("*"):
        p.unlink()
    try:
        frame_dir.rmdir()
    except OSError:
        pass


def main() -> None:
    day0 = datetime(2026, 7, 19, 16, 0, 0, tzinfo=timezone.utc)
    results = []
    # Sequential: asyncio.run inside threads is unsafe on Windows
    for lesson in LESSONS:
        results.append(process_one(lesson, day0))

    index = {
        "cycle": "stickman_forge_cycle_001",
        "series": "Ferrum Doctrine Stickman Combat Lessons",
        "channel": "The Tyrrell Codex",
        "count": len(results),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lessons": results,
        "status": "review",
        "note": "Ready for Authoritas review then Publicator short-form upload.",
    }
    out_idx = ROOT / "content_core" / "stickman_lessons" / "CYCLE_001_INDEX.json"
    out_idx.parent.mkdir(parents=True, exist_ok=True)
    out_idx.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    # sample manifest already written for lesson_01
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
