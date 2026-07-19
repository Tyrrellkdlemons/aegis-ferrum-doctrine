#!/usr/bin/env python3
"""Phoenix re-render (001) + future content buffer (002-004) with hook-optimized visuals."""

from __future__ import annotations

import asyncio
import json
import math
import os
import random
import struct
import subprocess
import wave
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG

PALETTE = {
    "bg": (8, 10, 14),
    "panel": (18, 22, 30),
    "blood": (193, 18, 31),
    "ember": (255, 77, 58),
    "steel": (168, 178, 193),
    "text": (245, 247, 250),
    "muted": (120, 130, 142),
    "gold": (232, 197, 71),
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def font(size: int):
    for c in [
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\seguisb.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]:
        if os.path.exists(c):
            return ImageFont.truetype(c, size=size)
    return ImageFont.load_default()


def cinematic_bg(w: int, h: int, seed: int = 0) -> Image.Image:
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (w, h), PALETTE["bg"])
    px = img.load()
    # vertical vignette + noise
    for y in range(h):
        for x in range(0, w, 2):
            n = int(rng.integers(0, 22))
            fall = int(40 * (1 - abs(x - w / 2) / (w / 2)) ** 2)
            v = min(255, n + fall // 3)
            px[x, y] = (8 + v // 5, 10 + v // 6, 14 + v // 4)
            if x + 1 < w:
                px[x + 1, y] = px[x, y]
    draw = ImageDraw.Draw(img)
    # blood edge bar
    draw.rectangle([0, 0, 18, h], fill=PALETTE["blood"])
    # tactical grid
    for x in range(40, w, 48):
        draw.line([(x, 0), (x, h)], fill=(30, 36, 46), width=1)
    for y in range(40, h, 48):
        draw.line([(0, y), (w, y)], fill=(30, 36, 46), width=1)
    # diagonal slash
    draw.polygon([(w - 420, 0), (w, 0), (w, 180), (w - 260, 0)], fill=(40, 12, 16))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return ImageEnhance.Contrast(img).enhance(1.25)


def draw_hook_card(path: Path, hook: str, sub: str, w: int = 1920, h: int = 1080, seed: int = 1) -> None:
    img = cinematic_bg(w, h, seed)
    draw = ImageDraw.Draw(img)
    # statue-ish silhouette block
    cx, cy = int(w * 0.78), int(h * 0.55)
    draw.ellipse([cx - 90, 120, cx + 90, 300], fill=(36, 40, 48))
    draw.polygon([(cx - 200, h - 80), (cx + 200, h - 80), (cx + 130, 280), (cx - 130, 280)], fill=(28, 32, 40))
    draw.polygon([(cx + 30, 160), (cx + 120, 140), (cx + 90, 320), (cx + 10, 330)], fill=PALETTE["blood"])
    # hook text with wrap
    f_hook = font(72 if len(hook) < 28 else 56)
    f_sub = font(36)
    draw.text((70, 160), hook, fill=PALETTE["text"], font=f_hook)
    draw.rectangle([70, 280, 520, 288], fill=PALETTE["blood"])
    draw.multiline_text((70, 320), sub, fill=PALETTE["steel"], font=f_sub, spacing=10)
    draw.text((70, h - 90), "FERRUM DOCTRINE", fill=PALETTE["muted"], font=font(28))
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")


def make_thumbnail(path: Path, line1: str, line2: str, sting: str) -> None:
    img = cinematic_bg(1280, 720, seed=99)
    draw = ImageDraw.Draw(img)
    cx = 980
    draw.ellipse([cx - 110, 80, cx + 110, 300], fill=(40, 44, 52))
    draw.polygon([(cx - 220, 680), (cx + 220, 680), (cx + 150, 280), (cx - 150, 280)], fill=(32, 36, 44))
    draw.polygon([(cx + 40, 150), (cx + 150, 120), (cx + 120, 340), (cx + 20, 350)], fill=PALETTE["blood"])
    draw.text((50, 140), line1, fill=PALETTE["text"], font=font(78))
    draw.text((50, 240), line2, fill=PALETTE["blood"], font=font(78))
    draw.text((50, 360), sting, fill=PALETTE["gold"], font=font(40))
    draw.rectangle([50, 430, 380, 438], fill=PALETTE["blood"])
    draw.text((50, 640), "FERRUM DOCTRINE", fill=PALETTE["muted"], font=font(26))
    ImageEnhance.Contrast(img).enhance(1.4).save(path)


PHOENIX_VOICE = """
Most men will never be dangerous. Not because the world is unfair — because they volunteered to be soft, then lied to themselves about why.

Let's drop the costume language.

You were sold a story: that comfort is self-care, that friction is trauma, that ambition is toxic, that a man who can hold his frame under pressure is somehow the problem. That story did not make you kind. It made you optional. Easy to ignore. Easy to replace. Easy to manage.

Danger is not screaming. Danger is not punching down. Danger is optionality under pressure — the ability to walk into a room with a calm nervous system, read the power map, keep three moves alive when everyone else has one, and leave without begging for approval. Soft men call that toxic. Operators call it adulthood.

The real reason most men stay weak: not genetics, not society — consent.

Every day you consent to the feed over the work. The snack over the set. The polite lie over the clean truth. The room that dilutes you over the exit that would save you. You do not lack information. You lack the willingness to be disliked while you rebuild.

Comfort is your religion. The second friction appears, you narcotize — scroll, porn, food, noise. Your nervous system has been trained like a pet.

You perform masculinity instead of earning it. Quotes. Cold showers for the camera. Statue filters. Then a real decision threatens status or sex or money and you fold like paper.

You confuse numbness with Stoicism. Marcus Aurelius did not write so you could ghost your own emotions and call it philosophy. Going blank is cowardice with better branding. Command is accurate perception plus deliberate action.

You have no drills. Motivation is a mood. Capability is rehearsal. Under stress, unrehearsed men become passengers in their own body.

If that offends you, good. Offense is cheaper than mediocrity and lasts five minutes.

A dangerous man is not a thug. A thug is predictable and disposable. A dangerous man keeps promises to himself when nobody is watching. He can tell the truth without needing cruelty as a costume. He can stay in a hard room without collapsing into people-pleasing. He can leave a soft room without a speech. He does not outsource his edges to women, bosses, algorithms, or the vibe.

The world does not reward your potential. It rewards your enforced standards.

Twenty-one days. No theater.

Drill one: discomfort budget. One hard physical act daily you do not feel like doing. Soft men wait to feel ready. Operators schedule readiness out of existence.

Drill two: silence interval. Ten minutes. No phone. Sit in the urge to escape.

Drill three: unsoftened truth. Once per day, say one true thing you have been sanding down for social ease. If your relationships require you to lie to stay liked, you do not have relationships. You have hostages.

Drill four: power map. Enter any space. Ten seconds. Exits. Status. Anxiety. Unspoken rule. Speak second.

Drill five: delayed strike. When provoked, do not answer from ego. Timing is how men keep power.

Drill six: one non-negotiable. Sleep, training, or deep work before noon. Break it and restart the count. Self-trust is the weapon.

Drill seven: controlled exit. Leave one diluting environment daily without announcing your transformation. Soft men stay to be liked. Dangerous men leave to stay sharp.

Nobody is coming. Not the algorithm. Not a woman. Not a mentor who will care more about your life than you do. You either build a counter-protocol or you become inventory.

Stoicism without standards is LARPing. Discipline without truth is gym cosplay. Mental health without agency is a subscription to your own weakness.

You want respect? Stop negotiating with the part of you that wants to stay soft.

If pressure hit in the next hour — money, status, conflict, body — do you have options, or excuses? Options means you trained. Excuses means you performed.

If you are done performing toughness and ready to train it — comment OPERATIVE. Subscribe for the next field manual. The soft path is crowded on purpose. Empty hard paths are where men are forged.
""".strip()


async def tts(text: str, out: Path, voice: str = "en-US-ChristopherNeural") -> None:
    import edge_tts

    out.parent.mkdir(parents=True, exist_ok=True)
    # Christopher = deeper; slow slightly for command presence
    communicate = edge_tts.Communicate(text, voice=voice, rate="-6%", pitch="-4Hz")
    await communicate.save(str(out))


def ambient(out: Path, seconds: float = 220.0) -> None:
    sr = 44100
    n = int(seconds * sr)
    t = np.arange(n, dtype=np.float32) / sr
    sig = (
        0.16 * np.sin(2 * np.pi * 48 * t)
        + 0.11 * np.sin(2 * np.pi * 72 * t + 0.4)
        + 0.07 * np.sin(2 * np.pi * 96 * t * (1 + 0.0015 * np.sin(0.07 * t)))
        + 0.03 * np.sin(2 * np.pi * 0.12 * t)
    )
    rng = np.random.default_rng(7)
    sig += 0.012 * (rng.random(n, dtype=np.float32) * 2 - 1)
    fade = np.minimum(1.0, t / 1.5) * np.minimum(1.0, (seconds - t) / 2.5)
    pcm = (np.clip(sig * fade * 0.5, -1, 1) * 30000).astype(np.int16)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def mix(voice: Path, music: Path, out: Path) -> float:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG, "-y", "-i", str(voice), "-i", str(music),
        "-filter_complex",
        "[1:a]volume=0.14[a1];[0:a]volume=1.05[a0];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-15:TP=-1.5:LRA=11[aout]",
        "-map", "[aout]", str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    probe = subprocess.run([FFMPEG, "-i", str(out)], capture_output=True, text=True)
    for line in (probe.stderr or "").splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 120.0


def assemble(audio: Path, scenes: list[Path], long_out: Path, short_out: Path, reel_out: Path) -> None:
    dur = mix_duration = None
    probe = subprocess.run([FFMPEG, "-i", str(audio)], capture_output=True, text=True)
    dur = 120.0
    for line in (probe.stderr or "").splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            dur = int(h) * 3600 + int(m) * 60 + float(s)
            break
    per = max(2.8, dur / max(1, len(scenes)))
    list_file = long_out.parent / "phoenix_concat.txt"
    lines = []
    for img in scenes:
        lines.append(f"file '{img.resolve().as_posix()}'")
        lines.append(f"duration {per:.3f}")
    lines.append(f"file '{scenes[-1].resolve().as_posix()}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Hook caption burn-in first 8s via drawtext
    vf = (
        "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,format=yuv420p,"
        "drawtext=fontfile=/Windows/Fonts/arialbd.ttf:text='COMMENT OPERATIVE':"
        "x=(w-text_w)/2:y=h-90:fontsize=36:fontcolor=white:"
        "borderw=2:bordercolor=black@0.6:enable='gte(t,8)'"
    )
    # Windows font path for ffmpeg
    fontfile = r"C\:/Windows/Fonts/arialbd.ttf"
    vf = (
        f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,format=yuv420p,"
        f"drawtext=fontfile='{fontfile}':text='FERRUM DOCTRINE':"
        f"x=40:y=40:fontsize=28:fontcolor=white@0.85:borderw=1:bordercolor=black,"
        f"drawtext=fontfile='{fontfile}':text='COMMENT OPERATIVE':"
        f"x=(w-text_w)/2:y=h-80:fontsize=34:fontcolor=0xC1121F:"
        f"borderw=2:bordercolor=black:enable='gte(t\\,12)'"
    )
    long_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-i", str(audio),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
        str(long_out),
    ]
    print("Encoding long...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # fallback without drawtext
        cmd2 = [
            FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-i", str(audio),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
            str(long_out),
        ]
        subprocess.run(cmd2, check=True, capture_output=True)

    for dest in (short_out, reel_out):
        subprocess.run(
            [
                FFMPEG, "-y", "-i", str(long_out), "-t", "55",
                "-vf", "crop=ih*9/16:ih,scale=1080:1920,fps=30,format=yuv420p",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                str(dest),
            ],
            check=True,
            capture_output=True,
        )
        print("Encoded", dest.name)


FUTURE = [
    {
        "id": "ferrum-doctrine-002",
        "slug": "soft_habits_kill_ambition",
        "title": "Soft Habits That Quietly Kill Ambition (Before You Notice)",
        "hook": "Your ambition didn't die in a crisis. It bled out in habits you call 'harmless.'",
        "schedule_offset_days": 1,
        "body_beats": [
            "The kill is quiet: snooze, 'quick check,' late sugar, open loops, yes-man agreements.",
            "Soft habits win because they feel like rest while they steal standards.",
            "Ambition without a kill-list is cosplay. Name the three habits that own you.",
            "Replacement protocol: one hard morning block, one friction gate on the phone, one nightly shutdown.",
            "If you keep the soft habit, stop calling yourself ambitious. Call yourself entertained.",
        ],
        "cta": "Comment KILL LIST with the habit you're executing this week.",
        "thumb": ("SOFT HABITS", "KILL YOU", "QUIT THE BLEED"),
    },
    {
        "id": "ferrum-doctrine-003",
        "slug": "spy_method_read_any_room",
        "title": "The Spy Method: Read Any Room in 10 Seconds",
        "hook": "Speak first and you lose. Read first and you own the next five minutes.",
        "schedule_offset_days": 2,
        "body_beats": [
            "Power maps beat small talk. Exits. Status. Anxiety. Unspoken rule. Performance vs substance.",
            "Most men talk to soothe insecurity. Operators gather terrain.",
            "Drill: ten-second scan before every meeting, gym, dinner, Discord call.",
            "Then speak second — short, aimed, no apology padding.",
            "Social intelligence is not niceness. It is accurate perception under pressure.",
        ],
        "cta": "Comment TERRAIN if you're running the ten-second scan for 7 days.",
        "thumb": ("READ THE", "ROOM", "SPEAK SECOND"),
    },
    {
        "id": "ferrum-doctrine-004",
        "slug": "mental_fortress_digital_noise",
        "title": "Build a Mental Fortress Against Digital Noise",
        "hook": "If your attention is for rent, your life is already owned.",
        "schedule_offset_days": 3,
        "body_beats": [
            "The feed is not entertainment. It is a weapons system aimed at your standards.",
            "Fortress rules: no phone in first 60 minutes, one deep-work bunker, notification famine.",
            "Dopamine is not the enemy. Untrained dopamine is.",
            "Replace scroll with silence intervals and one hard promise kept daily.",
            "Sovereignty starts where the algorithm loses access.",
        ],
        "cta": "Comment FORTRESS if you're locking the first hour tomorrow.",
        "thumb": ("YOUR MIND", "IS RENTED", "TAKE IT BACK"),
    },
]


def write_future_script(item: dict) -> Path:
    core = ROOT / "content_core" / "future" / f"{item['slug']}.md"
    core.parent.mkdir(parents=True, exist_ok=True)
    beats = "\n\n".join(f"### Beat {i+1}\n{b}" for i, b in enumerate(item["body_beats"]))
    text = f"""# MASTER SCRIPT — {item['id'].upper()}

**Title:** {item['title']}  
**Brand:** Ferrum Doctrine  
**Content ID:** {item['id']}  
**Retention design:** Hook in 0–3s · pattern interrupt every ~20s · open loop until CTA  
**Voice:** Field commander. No apology.

## HOOK (0–3s)
{item['hook']}

## BODY
{beats}

## CTA
{item['cta']}  
Subscribe for the next Ferrum Doctrine field manual.

## SHORTS HOOKS
1. {item['hook']}
2. Soft men negotiate with their weakest hour. Operators schedule it out of existence.
3. Comment the keyword. Do the drill. Stop performing.
"""
    core.write_text(text, encoding="utf-8")
    return core


def stage_future_platform(item: dict, day0: datetime) -> None:
    when = day0 + timedelta(days=item["schedule_offset_days"])
    # youtube pack
    yt = ROOT / "platforms" / "buffer" / item["id"] / "youtube"
    yt.mkdir(parents=True, exist_ok=True)
    make_thumbnail(yt / "thumbnail_final.png", *item["thumb"])
    # placeholder media note + hook cards as interim assets
    for i, beat in enumerate(item["body_beats"][:6]):
        draw_hook_card(
            yt / f"scene_{i+1:02d}.png",
            item["hook"][:42] if i == 0 else f"BEAT {i}",
            beat[:120],
            seed=200 + i,
        )
    (yt / "VOICEOVER_PENDING.txt").write_text(
        f"Render VO from content_core/future/{item['slug']}.md then assemble.\n",
        encoding="utf-8",
    )
    (yt / "final_long.mp4.PLACEHOLDER").write_text(
        "Awaiting phoenix-quality assemble after VO. Export: 1920x1080, 30fps, H.264 CRF18, AAC 256k.\n",
        encoding="utf-8",
    )
    manifest = {
        "platform": "youtube",
        "content_id": item["id"],
        "file": "final_long.mp4",
        "title": f"{item['title']} | Ferrum Doctrine",
        "description": (
            f"{item['hook']}\n\n"
            f"{item['cta']}\n\n"
            "Ferrum Doctrine — discipline without apology.\n"
        ),
        "tags": [
            "ferrum doctrine", "discipline", "stoicism for men", "self improvement men",
            "mental toughness", "masculine presence", "anti comfort", "self mastery",
            "hard truths for men", "focus", "habit building", "sovereignty",
        ],
        "thumbnail": "thumbnail_final.png",
        "schedule": when.replace(hour=12, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "queued_buffer",
        "retention_hooks": [item["hook"], "pattern interrupt every 20s", item["cta"]],
        "monetization": {"midroll": True, "affiliate_links": [], "pinned_comment": item["cta"]},
    }
    atomic_json(yt / "publish_manifest.json", manifest)
    (yt / "WHAT_WHERE_WHEN.md").write_text(
        f"# {item['id']} YouTube\n\n- WHAT: {item['title']}\n"
        f"- WHERE: Ferrum Doctrine\n- WHEN: {manifest['schedule']}\n"
        f"- STATUS: buffer — VO+assemble pending\n",
        encoding="utf-8",
    )

    # shorts text packs
    for plat, fname, hour in [("tiktok", "caption.txt", 18), ("instagram", "caption.txt", 17), ("x", "thread.txt", 13)]:
        pdir = ROOT / "platforms" / "buffer" / item["id"] / plat
        pdir.mkdir(parents=True, exist_ok=True)
        if plat == "x":
            body = (
                f"1/ {item['hook']}\n\n"
                + "\n\n".join(f"{i+2}/ {b}" for i, b in enumerate(item["body_beats"][:5]))
                + f"\n\n7/ {item['cta']}\n"
            )
            (pdir / fname).write_text(body, encoding="utf-8")
        else:
            (pdir / fname).write_text(
                f"{item['hook']}\n\n{item['cta']}\n\n#discipline #stoicism #masculinity #ferrumdoctrine #mindset\n",
                encoding="utf-8",
            )
        atomic_json(
            pdir / "publish_manifest.json",
            {
                "platform": plat,
                "content_id": item["id"],
                "file": fname,
                "title": item["title"],
                "description": open(pdir / fname, encoding="utf-8").read(),
                "tags": ["discipline", "stoicism", "masculinity", "ferrumdoctrine"],
                "thumbnail": None,
                "schedule": when.replace(hour=hour, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "queued_buffer",
                "monetization": {"midroll": False, "affiliate_links": [], "pinned_comment": ""},
            },
        )


def main() -> None:
    print("[1] Phoenix VO...")
    voice = ROOT / "assets/voice/ferrum_doctrine_001_phoenix.mp3"
    music = ROOT / "assets/voice/ferrum_doctrine_001_music.wav"
    mixed = ROOT / "assets/voice/ferrum_doctrine_001_final.wav"
    asyncio.run(tts(PHOENIX_VOICE, voice))
    ambient(music, seconds=240)
    dur = mix(voice, music, mixed)
    print("  duration", dur)

    print("[2] Hook-optimized scenes...")
    scene_dir = ROOT / "assets/visuals/phoenix_broll"
    hooks = [
        ("MOST MEN STAY SOFT", "They volunteered. Then lied about why."),
        ("COMFORT IS A RELIGION", "Friction appears. You narcotize."),
        ("PERFORMANCE ≠ POWER", "Statue filters fold under cost."),
        ("NUMBNESS ISN'T STOICISM", "Blank is cowardice with branding."),
        ("NO DRILLS = PASSENGER", "Motivation dies under stress."),
        ("DANGER = OPTIONS", "Three moves when others have one."),
        ("DRILL: DISCOMFORT", "Consent to friction on schedule."),
        ("DRILL: SILENCE", "Ten minutes. No escape."),
        ("DRILL: UNSOFTENED TRUTH", "Lies for likes are hostages."),
        ("DRILL: POWER MAP", "Read terrain. Speak second."),
        ("DRILL: DELAYED STRIKE", "Timing keeps power."),
        ("DRILL: EXIT", "Leave without a speech."),
        ("NOBODY IS COMING", "Build the counter-protocol."),
        ("OPTIONS OR EXCUSES", "Pressure test. Tonight."),
        ("COMMENT: OPERATIVE", "Hard paths are empty on purpose."),
    ]
    scenes = []
    for i, (h, s) in enumerate(hooks):
        p = scene_dir / f"scene_{i+1:02d}.png"
        draw_hook_card(p, h, s, seed=10 + i)
        scenes.append(p)

    thumb = ROOT / "platforms/youtube/thumbnail_final.png"
    make_thumbnail(thumb, "THEY LIE", "TO YOU", "STAY SOFT → STAY OWNED")
    # also core
    make_thumbnail(ROOT / "content_core" / "thumbnail_final.png", "THEY LIE", "TO YOU", "STAY SOFT → STAY OWNED")

    print("[3] Assemble platform media...")
    long_p = ROOT / "platforms/youtube/final_long.mp4"
    short_p = ROOT / "platforms/youtube/final_short.mp4"
    reel_p = ROOT / "platforms/instagram/final_reel.mp4"
    tik_p = ROOT / "platforms/tiktok/final_tiktok.mp4"
    assemble(mixed, scenes, long_p, short_p, reel_p)
    # copy short to tiktok
    import shutil

    shutil.copy2(short_p, tik_p)
    # archive copies
    shutil.copy2(long_p, ROOT / "assets/final/ferrum_doctrine_001_phoenix_long.mp4")
    shutil.copy2(short_p, ROOT / "assets/final/ferrum_doctrine_001_phoenix_short.mp4")

    # update youtube manifest
    man_path = ROOT / "platforms/youtube/publish_manifest.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man["status"] = "ready_pending_authoritas"
    man["audio_source"] = "assets/voice/ferrum_doctrine_001_phoenix.mp3"
    man["script_source"] = "content_core/master_script.md"
    man["render"] = "phoenix_v1"
    atomic_json(man_path, man)

    print("[4] Future buffer 002-004...")
    day0 = datetime(2026, 7, 19, tzinfo=timezone.utc)
    buffer_sched = []
    for item in FUTURE:
        write_future_script(item)
        stage_future_platform(item, day0)
        buffer_sched.append(
            {
                "content_id": item["id"],
                "title": item["title"],
                "when": (day0 + timedelta(days=item["schedule_offset_days"])).strftime("%Y-%m-%dT12:00:00Z"),
                "status": "queued_buffer",
                "hook": item["hook"],
            }
        )
    atomic_json(ROOT / "platforms/buffer/BUFFER_SCHEDULE.json", {"generated_at": now_iso(), "items": buffer_sched})

    # update dashboard schedule data
    dash = {
        "content_id": "ferrum-doctrine-pipeline",
        "brutality_score": 93,
        "brand": "Ferrum Doctrine",
        "posts": [
            {"platform": "youtube", "piece": "001 Phoenix long", "when": "2026-07-19T12:00:00Z", "status": "ready", "file": "final_long.mp4"},
            {"platform": "x", "piece": "001 thread", "when": "2026-07-19T13:00:00Z", "status": "ready", "file": "thread.txt"},
            {"platform": "instagram", "piece": "001 reel", "when": "2026-07-19T17:00:00Z", "status": "ready", "file": "final_reel.mp4"},
            {"platform": "tiktok", "piece": "001 short", "when": "2026-07-19T18:30:00Z", "status": "ready", "file": "final_tiktok.mp4"},
            {"platform": "reddit", "piece": "001 post", "when": "2026-07-20T15:00:00Z", "status": "ready", "file": "post.md"},
        ]
        + [
            {
                "platform": "youtube",
                "piece": f"{b['content_id']} (buffer)",
                "when": b["when"],
                "status": "queued_buffer",
                "file": "pending_vo",
            }
            for b in buffer_sched
        ],
    }
    atomic_json(ROOT / "dashboard/data/schedule.json", dash)
    atomic_json(ROOT / "docs/data/schedule.json", dash)

    print("DONE", long_p.stat().st_size if long_p.exists() else 0)


if __name__ == "__main__":
    main()
