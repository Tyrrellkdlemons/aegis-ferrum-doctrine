#!/usr/bin/env python3
"""
STICKMAN FORGE V2 — Ferrum Doctrine cinematic vertical combat lessons.

Benchmarked against viral stickman Shorts / Reels (Rico-style fight energy,
anime impact frames, CapCut fight-edit pacing):
  - continuous pose interpolation (not 4 static holds)
  - camera shake, hit flashes, speed lines, afterimages
  - kinetic captions (2–5 words slamming on beat)
  - procedural hit/whoosh SFX under VO
  - 1080x1920 @ 30fps, high bitrate
  - punchier ~22–32s VO for retention (full doctrine scripts still stored)

Requires: pillow, numpy, scipy, edge-tts, imageio-ffmpeg
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import struct
import subprocess
import wave
from datetime import datetime, timezone, timedelta
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FPS = 30
RED = (193, 18, 31)
WHITE = (245, 245, 245)
GRAY = (110, 110, 110)
DIM = (40, 40, 40)

# Joint pack: hip_dx, sh_dy, la, ra, ll, rl  (angles deg from down; + = viewer's right)
POSES: dict[str, tuple[float, float, float, float, float, float]] = {
    "idle": (0, 0, -18, 18, -10, 10),
    "guard": (0, -12, -115, 45, -18, 22),
    "advance": (18, -8, -95, 35, -42, 28),
    "strike": (-8, -28, -165, 70, -30, 40),
    "uppercut": (-4, -35, -40, -175, -20, 35),
    "kick": (10, -10, -80, 40, -15, 95),
    "submit": (0, 45, 45, 55, 40, -40),
    "fall": (55, 70, 90, 110, 75, 55),
    "point": (0, -12, -25, -175, -12, 18),
    "train": (0, -18, -160, -45, -22, 32),
    "power": (0, -40, -140, -140, -25, 25),
    "crouch": (0, 25, -90, 40, -50, 50),
}

LESSONS = [
    {
        "id": "lesson_01",
        "title": "Comfort Is a Cage",
        "hook": "Your comfort is not rest. It is a cage you decorate.",
        "body": "Every easy hit — scroll, snack, snooze — trains you to flinch from friction. Soft men call it balance. Operators call it surrender. You do not escape a cage by polishing the bars.",
        "demand": "Cut one comfort ritual tomorrow morning. Miss it and you chose the cage. Decide.",
        "combat": "cage",
        "vo": (
            "Your comfort is not rest. It is a cage you decorate. "
            "Scroll. Snack. Snooze. Soft men call it balance. Operators call it surrender. "
            "You do not escape a cage by polishing the bars. "
            "Cut one comfort ritual tomorrow. Or stay locked. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.14, "COMFORT IS A CAGE", RED),
            (0.14, 0.32, "SCROLL. SNACK. SNOOZE.", WHITE),
            (0.32, 0.52, "THAT IS SURRENDER", RED),
            (0.52, 0.72, "STOP POLISHING BARS", WHITE),
            (0.72, 0.90, "CUT ONE RITUAL", RED),
            (0.90, 1.01, "DECIDE.", WHITE),
        ],
    },
    {
        "id": "lesson_02",
        "title": "Respect Is Earned Under Pressure",
        "hook": "Most men die without ever being respected. Here's why.",
        "body": "Respect is not requested. It is the residue of kept standards when it costs you. Perform toughness online and fold offline — and you become optional. Pressure is the only exam that counts.",
        "demand": "Keep one hard promise for seven days. Break it and restart. Or stay invisible. Decide.",
        "combat": "duel_win",
        "vo": (
            "Most men die without ever being respected. Here's why. "
            "Respect is not requested. It is kept standards when it costs you. "
            "Tough online. Soft offline. You become optional. "
            "Keep one hard promise seven days. Or stay invisible. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.16, "RESPECT IS EARNED", RED),
            (0.16, 0.38, "UNDER PRESSURE", WHITE),
            (0.38, 0.58, "STANDARDS THAT COST", RED),
            (0.58, 0.78, "ONE HARD PROMISE", WHITE),
            (0.78, 1.01, "SEVEN DAYS. DECIDE.", RED),
        ],
    },
    {
        "id": "lesson_03",
        "title": "Your Phone Owns You",
        "hook": "If your attention is for rent, your life is already owned.",
        "body": "The feed is not entertainment. It is a weapons system aimed at your standards. Soft men negotiate with the algorithm. Operators cut the pipe. Sovereignty starts where the phone loses access.",
        "demand": "First sixty minutes tomorrow — no phone. Fail and you stay leased. Decide.",
        "combat": "phone_smash",
        "vo": (
            "If your attention is for rent, your life is already owned. "
            "The feed is a weapons system aimed at your standards. "
            "Soft men negotiate. Operators cut the pipe. "
            "First sixty minutes tomorrow — no phone. Or stay leased. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.16, "YOUR PHONE OWNS YOU", RED),
            (0.16, 0.40, "ATTENTION FOR RENT", WHITE),
            (0.40, 0.62, "CUT THE PIPE", RED),
            (0.62, 0.85, "60 MINUTES. NO PHONE.", WHITE),
            (0.85, 1.01, "DECIDE.", RED),
        ],
    },
    {
        "id": "lesson_04",
        "title": "Cheap Pleasure Steals Your Frame",
        "hook": "You cannot lead a room when your nervous system is rented by cheap hits.",
        "body": "Porn, endless games, micro-rewards — they do not relax you. They flatten your hunger. A man with a rented reward system cannot hold frame, finish hard work, or tolerate boredom. That is not freedom. That is sedation.",
        "demand": "Thirty days without your cheapest hit. Or stay sedated. Decide.",
        "combat": "shadow_defeat",
        "vo": (
            "You cannot lead a room when cheap hits rent your nervous system. "
            "Porn. Games. Micro-rewards. They flatten your hunger. "
            "That is not freedom. That is sedation. "
            "Thirty days without your cheapest hit. Or stay soft. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.18, "CHEAP PLEASURE", RED),
            (0.18, 0.36, "STEALS YOUR FRAME", WHITE),
            (0.36, 0.58, "HUNGER FLATTENS", RED),
            (0.58, 0.80, "30 DAYS. NO CHEAP HIT.", WHITE),
            (0.80, 1.01, "DECIDE.", RED),
        ],
    },
    {
        "id": "lesson_05",
        "title": "Speak Second",
        "hook": "Speak first and you lose. Read first and you own the next five minutes.",
        "body": "Soft men talk to soothe insecurity. Operators gather terrain — exits, status, anxiety, unspoken rule. Ten seconds of silence beats ten minutes of noise. Social power is perception under pressure, not charm.",
        "demand": "Run a ten-second room scan before you speak — seven days. Or stay loud and weak. Decide.",
        "combat": "stance",
        "vo": (
            "Speak first and you lose. Read first and you own the next five minutes. "
            "Soft men talk to soothe insecurity. Operators gather terrain. "
            "Ten seconds of silence beats ten minutes of noise. "
            "Room scan before you speak. Seven days. Or stay loud and weak. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.16, "SPEAK SECOND", RED),
            (0.16, 0.38, "READ THE ROOM", WHITE),
            (0.38, 0.58, "SILENCE IS POWER", RED),
            (0.58, 0.82, "10-SECOND SCAN", WHITE),
            (0.82, 1.01, "DECIDE.", RED),
        ],
    },
    {
        "id": "lesson_06",
        "title": "Soft Habits Bleed Ambition",
        "hook": "Your ambition did not die in a crisis. It bled out in habits you call harmless.",
        "body": "Snooze. Quick check. Open loops. Yes-man agreements. Soft habits win because they feel like rest while they steal standards. Ambition without a kill-list is cosplay.",
        "demand": "Name three soft habits tonight. Kill one this week. Or stay entertained. Decide.",
        "combat": "bleed",
        "vo": (
            "Your ambition did not die in a crisis. It bled out in harmless habits. "
            "Snooze. Quick check. Open loops. Soft habits steal standards. "
            "Ambition without a kill-list is cosplay. "
            "Name three soft habits. Kill one this week. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.18, "SOFT HABITS", RED),
            (0.18, 0.38, "BLEED AMBITION", WHITE),
            (0.38, 0.60, "KILL THE LIST", RED),
            (0.60, 0.84, "KILL ONE THIS WEEK", WHITE),
            (0.84, 1.01, "DECIDE.", RED),
        ],
    },
    {
        "id": "lesson_07",
        "title": "Pain Is Tuition",
        "hook": "If growth never hurts, you are not growing. You are rearranging comfort.",
        "body": "Anti-fragility is built by voluntary stress on schedule — lift, cold, hard truth, deep work. Soft men wait to feel ready. Operators schedule readiness out of existence. Pain paid in advance is cheaper than pain collected by life.",
        "demand": "One discomfort budget daily for twenty-one days. Skip and you skipped the tuition. Decide.",
        "combat": "train",
        "vo": (
            "If growth never hurts, you are rearranging comfort. "
            "Lift. Cold. Hard truth. Deep work. Soft men wait to feel ready. "
            "Operators schedule readiness out of existence. "
            "One discomfort daily. Twenty-one days. Pay tuition. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.16, "PAIN IS TUITION", RED),
            (0.16, 0.38, "VOLUNTARY STRESS", WHITE),
            (0.38, 0.58, "SCHEDULE HARDSHIP", RED),
            (0.58, 0.82, "21 DAYS. DAILY.", WHITE),
            (0.82, 1.01, "DECIDE.", RED),
        ],
    },
    {
        "id": "lesson_08",
        "title": "Nobody Is Coming",
        "hook": "Nobody is coming to make you formidable.",
        "body": "Not the algorithm. Not a mentor who cares more than you do. Not a relationship that will install your spine. The soft machine is already running. You either build a counter-protocol or you become inventory.",
        "demand": "Write your counter-protocol tonight — three rules. Or stay inventory. Decide.",
        "combat": "alone",
        "vo": (
            "Nobody is coming to make you formidable. "
            "Not the algorithm. Not a mentor. Not a relationship. "
            "Build a counter-protocol or become inventory. "
            "Three rules tonight. Or stay inventory. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.18, "NOBODY IS COMING", RED),
            (0.18, 0.42, "NO SAVIOR", WHITE),
            (0.42, 0.64, "BUILD PROTOCOL", RED),
            (0.64, 0.86, "THREE RULES TONIGHT", WHITE),
            (0.86, 1.01, "DECIDE.", RED),
        ],
    },
    {
        "id": "lesson_09",
        "title": "Options Beat Excuses",
        "hook": "When pressure hits, soft men produce stories. Dangerous men produce options.",
        "body": "Options come from training: body, silence, truth, delayed reply, one non-negotiable. Excuses come from performance. Danger is not rage. Danger is optionality under pressure.",
        "demand": "Pressure-test tonight: money, status, body — options or excuses? Build one option tomorrow. Decide.",
        "combat": "fork",
        "vo": (
            "When pressure hits, soft men produce stories. Dangerous men produce options. "
            "Options come from training. Excuses come from performance. "
            "Danger is optionality under pressure. "
            "Build one option tomorrow. Or stay a storyteller. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.18, "OPTIONS > EXCUSES", RED),
            (0.18, 0.40, "PRESSURE HITS", WHITE),
            (0.40, 0.62, "TRAIN OPTIONALLY", RED),
            (0.62, 0.84, "BUILD ONE OPTION", WHITE),
            (0.84, 1.01, "DECIDE.", RED),
        ],
    },
    {
        "id": "lesson_10",
        "title": "One Non-Negotiable",
        "hook": "If everything is flexible, you are not disciplined. You are negotiable.",
        "body": "Self-trust is the weapon. One non-negotiable — sleep, training, or deep work — kept when nobody watches. Break it and restart the count. Without self-trust every system is costume.",
        "demand": "Pick one non-negotiable before midnight. Keep it twenty-one days. Or stay optional. Decide.",
        "combat": "oath",
        "vo": (
            "If everything is flexible, you are negotiable. "
            "Self-trust is the weapon. One non-negotiable. Kept when nobody watches. "
            "Break it and restart the count. "
            "Pick one before midnight. Twenty-one days. Or stay optional. Decide. Ferrum."
        ),
        "captions": [
            (0.00, 0.16, "ONE NON-NEGOTIABLE", RED),
            (0.16, 0.40, "SELF-TRUST = WEAPON", WHITE),
            (0.40, 0.62, "KEEP IT ALONE", RED),
            (0.62, 0.84, "21 DAYS. NO DEAL.", WHITE),
            (0.84, 1.01, "DECIDE.", RED),
        ],
    },
]


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for c in [
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\seguibl.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
    ]:
        if os.path.exists(c):
            return ImageFont.truetype(c, size=size)
    return ImageFont.load_default()


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_pose(pa: str, pb: str, t: float) -> tuple[float, ...]:
    a, b = POSES[pa], POSES[pb]
    t = ease_in_out(t)
    return tuple(lerp(x, y, t) for x, y in zip(a, b))


def end_pt(ox: float, oy: float, ang: float, length: float) -> tuple[int, int]:
    rad = math.radians(ang)
    return int(ox + length * math.sin(rad)), int(oy + length * math.cos(rad))


def draw_stick_params(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    params: tuple[float, ...],
    scale: float = 1.0,
    color: tuple[int, int, int] = WHITE,
    accent: bool = False,
    width_mul: float = 1.0,
) -> None:
    hip_dx, sh_dy, la, ra, ll, rl = params
    s = scale
    head_r = int(30 * s)
    w = max(4, int(6 * s * width_mul))
    hip = (cx + hip_dx * s, cy)
    shoulder = (cx + hip_dx * s, cy - 95 * s + sh_dy * s)
    head = (shoulder[0], shoulder[1] - head_r - 10 * s)

    # soft glow under feet
    draw.ellipse(
        [hip[0] - 55 * s, 1395, hip[0] + 55 * s, 1425],
        fill=(20, 20, 20),
    )

    draw.line([hip, shoulder], fill=color, width=w)
    draw.ellipse(
        [head[0] - head_r, head[1] - head_r, head[0] + head_r, head[1] + head_r],
        outline=color,
        width=w,
    )
    arm_len, leg_len = 74 * s, 90 * s
    lh = end_pt(shoulder[0], shoulder[1], la, arm_len)
    rh = end_pt(shoulder[0], shoulder[1], ra, arm_len)
    lf = end_pt(hip[0], hip[1], ll, leg_len)
    rf = end_pt(hip[0], hip[1], rl, leg_len)
    draw.line([shoulder, lh], fill=color, width=w)
    draw.line([shoulder, rh], fill=color, width=w)
    draw.line([hip, lf], fill=color, width=w)
    draw.line([hip, rf], fill=color, width=w)

    if accent:
        bw = 40 * s
        draw.rectangle(
            [hip[0] - bw, hip[1] - 7 * s, hip[0] + bw, hip[1] + 5 * s],
            fill=RED,
        )
        draw.line(
            [hip[0], hip[1], hip[0] + 12 * s, hip[1] + 32 * s],
            fill=RED,
            width=max(3, w - 1),
        )


def choreography(combat: str) -> list[dict]:
    """Timeline of moves as fractions of video (0–1). Each beat has fx flags."""
    # generic beat map reused / specialized
    charts = {
        "cage": [
            {"a": 0.00, "b": 0.18, "op": ("submit", "idle"), "en": None, "fx": "tension"},
            {"a": 0.18, "b": 0.38, "op": ("idle", "guard"), "en": None, "fx": "whoosh"},
            {"a": 0.38, "b": 0.55, "op": ("guard", "strike"), "en": None, "fx": "hit"},
            {"a": 0.55, "b": 0.72, "op": ("strike", "power"), "en": None, "fx": "hit"},
            {"a": 0.72, "b": 0.90, "op": ("power", "point"), "en": None, "fx": "whoosh"},
            {"a": 0.90, "b": 1.01, "op": ("point", "point"), "en": None, "fx": "sting"},
        ],
        "duel_win": [
            {"a": 0.00, "b": 0.18, "op": ("guard", "advance"), "en": ("guard", "guard"), "fx": "tension"},
            {"a": 0.18, "b": 0.40, "op": ("advance", "strike"), "en": ("guard", "fall"), "fx": "hit"},
            {"a": 0.40, "b": 0.58, "op": ("strike", "uppercut"), "en": ("fall", "fall"), "fx": "hit"},
            {"a": 0.58, "b": 0.78, "op": ("uppercut", "point"), "en": ("fall", "submit"), "fx": "whoosh"},
            {"a": 0.78, "b": 1.01, "op": ("point", "point"), "en": ("submit", "submit"), "fx": "sting"},
        ],
        "phone_smash": [
            {"a": 0.00, "b": 0.20, "op": ("idle", "guard"), "en": None, "fx": "tension"},
            {"a": 0.20, "b": 0.42, "op": ("guard", "strike"), "en": None, "fx": "whoosh"},
            {"a": 0.42, "b": 0.62, "op": ("strike", "kick"), "en": None, "fx": "hit"},
            {"a": 0.62, "b": 0.82, "op": ("kick", "point"), "en": None, "fx": "hit"},
            {"a": 0.82, "b": 1.01, "op": ("point", "point"), "en": None, "fx": "sting"},
        ],
        "shadow_defeat": [
            {"a": 0.00, "b": 0.18, "op": ("guard", "advance"), "en": ("advance", "guard"), "fx": "tension"},
            {"a": 0.18, "b": 0.40, "op": ("advance", "strike"), "en": ("guard", "fall"), "fx": "hit"},
            {"a": 0.40, "b": 0.62, "op": ("strike", "power"), "en": ("fall", "submit"), "fx": "hit"},
            {"a": 0.62, "b": 0.84, "op": ("power", "point"), "en": ("submit", "submit"), "fx": "whoosh"},
            {"a": 0.84, "b": 1.01, "op": ("point", "point"), "en": ("submit", "submit"), "fx": "sting"},
        ],
        "stance": [
            {"a": 0.00, "b": 0.22, "op": ("idle", "guard"), "en": None, "fx": "tension"},
            {"a": 0.22, "b": 0.45, "op": ("guard", "guard"), "en": None, "fx": "scan"},
            {"a": 0.45, "b": 0.68, "op": ("guard", "point"), "en": None, "fx": "whoosh"},
            {"a": 0.68, "b": 0.88, "op": ("point", "guard"), "en": None, "fx": "tension"},
            {"a": 0.88, "b": 1.01, "op": ("guard", "point"), "en": None, "fx": "sting"},
        ],
        "bleed": [
            {"a": 0.00, "b": 0.20, "op": ("submit", "idle"), "en": None, "fx": "tension"},
            {"a": 0.20, "b": 0.42, "op": ("idle", "crouch"), "en": None, "fx": "whoosh"},
            {"a": 0.42, "b": 0.64, "op": ("crouch", "guard"), "en": None, "fx": "hit"},
            {"a": 0.64, "b": 0.84, "op": ("guard", "advance"), "en": None, "fx": "whoosh"},
            {"a": 0.84, "b": 1.01, "op": ("advance", "point"), "en": None, "fx": "sting"},
        ],
        "train": [
            {"a": 0.00, "b": 0.18, "op": ("train", "strike"), "en": None, "fx": "hit"},
            {"a": 0.18, "b": 0.36, "op": ("strike", "train"), "en": None, "fx": "whoosh"},
            {"a": 0.36, "b": 0.54, "op": ("train", "kick"), "en": None, "fx": "hit"},
            {"a": 0.54, "b": 0.74, "op": ("kick", "power"), "en": None, "fx": "hit"},
            {"a": 0.74, "b": 1.01, "op": ("power", "guard"), "en": None, "fx": "sting"},
        ],
        "alone": [
            {"a": 0.00, "b": 0.25, "op": ("idle", "guard"), "en": None, "fx": "tension"},
            {"a": 0.25, "b": 0.50, "op": ("guard", "point"), "en": None, "fx": "whoosh"},
            {"a": 0.50, "b": 0.75, "op": ("point", "power"), "en": None, "fx": "hit"},
            {"a": 0.75, "b": 1.01, "op": ("power", "point"), "en": None, "fx": "sting"},
        ],
        "fork": [
            {"a": 0.00, "b": 0.20, "op": ("guard", "point"), "en": ("submit", "submit"), "fx": "tension"},
            {"a": 0.20, "b": 0.42, "op": ("point", "advance"), "en": ("submit", "fall"), "fx": "whoosh"},
            {"a": 0.42, "b": 0.64, "op": ("advance", "strike"), "en": ("fall", "fall"), "fx": "hit"},
            {"a": 0.64, "b": 0.84, "op": ("strike", "point"), "en": ("fall", "submit"), "fx": "hit"},
            {"a": 0.84, "b": 1.01, "op": ("point", "point"), "en": ("submit", "submit"), "fx": "sting"},
        ],
        "oath": [
            {"a": 0.00, "b": 0.22, "op": ("guard", "idle"), "en": None, "fx": "tension"},
            {"a": 0.22, "b": 0.45, "op": ("idle", "point"), "en": None, "fx": "whoosh"},
            {"a": 0.45, "b": 0.68, "op": ("point", "power"), "en": None, "fx": "hit"},
            {"a": 0.68, "b": 0.88, "op": ("power", "guard"), "en": None, "fx": "whoosh"},
            {"a": 0.88, "b": 1.01, "op": ("guard", "point"), "en": None, "fx": "sting"},
        ],
    }
    return charts.get(combat, charts["alone"])


def active_beat(chart: list[dict], t: float) -> tuple[dict, float]:
    for beat in chart:
        if beat["a"] <= t < beat["b"] or (t >= 1.0 and beat is chart[-1]):
            local = (t - beat["a"]) / max(1e-6, beat["b"] - beat["a"])
            return beat, max(0.0, min(1.0, local))
    return chart[-1], 1.0


def caption_at(captions: list[tuple], t: float) -> tuple[str, tuple[int, int, int]]:
    for a, b, text, col in captions:
        if a <= t < b:
            return text, col
    return captions[-1][2], captions[-1][3]


def draw_speed_lines(draw: ImageDraw.ImageDraw, intensity: float, side: str = "right") -> None:
    if intensity < 0.15:
        return
    rng = np.random.default_rng(int(intensity * 1000) % 997)
    n = int(18 * intensity)
    for _ in range(n):
        y = int(rng.integers(500, 1450))
        length = int(rng.integers(80, 280) * intensity)
        if side == "right":
            x0 = int(rng.integers(600, 1000))
            draw.line([(x0, y), (x0 + length, y - int(10 * intensity))], fill=(70, 70, 70), width=2)
        else:
            x0 = int(rng.integers(80, 480))
            draw.line([(x0, y), (x0 - length, y - int(10 * intensity))], fill=(70, 70, 70), width=2)


def draw_impact_burst(draw: ImageDraw.ImageDraw, x: int, y: int, strength: float) -> None:
    if strength < 0.2:
        return
    r = int(40 + 120 * strength)
    for i in range(8):
        ang = i * 45 + strength * 40
        x2, y2 = end_pt(x, y, ang - 90, r)
        draw.line([(x, y), (x2, y2)], fill=RED, width=max(2, int(4 * strength)))
    draw.ellipse([x - 18, y - 18, x + 18, y + 18], outline=WHITE, width=3)


def render_frame(lesson: dict, t: float, shake: tuple[float, float], flash: float) -> Image.Image:
    # deep charcoal + vignette atmosphere (not flat black slideshow)
    img = Image.new("RGB", (W, H), (8, 8, 10))
    draw = ImageDraw.Draw(img)

    # vertical gradient strips
    for y in range(0, H, 4):
        v = int(8 + 18 * (y / H))
        draw.line([(0, y), (W, y)], fill=(v, v, v + 2))

    # subtle arena grid
    for x in range(0, W, 80):
        draw.line([(x, 600), (x, 1450)], fill=(22, 22, 26), width=1)
    for y in range(600, 1450, 80):
        draw.line([(60, y), (1020, y)], fill=(22, 22, 26), width=1)

    # brand bar
    draw.rectangle([0, 0, W, 10], fill=RED)
    draw.text((36, 36), "FERRUM DOCTRINE", fill=(90, 90, 95), font=font(26))
    draw.text((36, 72), "STICKMAN COMBAT LESSON", fill=(55, 55, 60), font=font(22))

    sx, sy = shake
    chart = choreography(lesson["combat"])
    beat, local = active_beat(chart, t)
    op_params = lerp_pose(beat["op"][0], beat["op"][1], local)
    fx = beat["fx"]

    hip_y = 1180 + sy
    combat = lesson["combat"]

    # afterimage on strikes
    if fx == "hit" and local < 0.45:
        ghost = lerp_pose(beat["op"][0], beat["op"][1], max(0.0, local - 0.18))
        draw_stick_params(draw, 340 + sx - 40, hip_y, ghost, 1.25, (60, 60, 70), accent=False, width_mul=0.7)

    impact_strength = 0.0
    if fx == "hit":
        impact_strength = ease_out_cubic(1.0 - abs(local - 0.35) * 2.5) if local < 0.7 else 0.0
        draw_speed_lines(draw, impact_strength, "right")

    if combat == "cage":
        # cage bars that crack on hit
        for i, x in enumerate(range(180, 920, 70)):
            cracked = fx == "hit" and local > 0.3 and i in (3, 4, 5)
            col = (90, 30, 35) if cracked else (55, 55, 60)
            draw.line([(x + sx, 720 + sy), (x + sx, 1400 + sy)], fill=col, width=5)
            if cracked:
                draw.line([(x + sx, 1000), (x + sx + 25, 1040)], fill=RED, width=3)
        draw_stick_params(draw, 540 + sx, hip_y, op_params, 1.4, WHITE, accent=True)
        if impact_strength > 0.3:
            draw_impact_burst(draw, int(540 + sx), int(980 + sy), impact_strength)

    elif combat in ("duel_win", "shadow_defeat", "fork"):
        en_params = lerp_pose(beat["en"][0], beat["en"][1], local) if beat["en"] else POSES["guard"]
        en_y = hip_y + (90 if beat["en"] and "fall" in beat["en"] and local > 0.4 else 0)
        draw_stick_params(draw, 340 + sx, hip_y, op_params, 1.32, WHITE, accent=True)
        draw_stick_params(draw, 760 + sx, en_y, en_params, 1.2, GRAY, accent=False)
        if impact_strength > 0.25:
            draw_impact_burst(draw, int(560 + sx), int(1000 + sy), impact_strength)
        if combat == "fork":
            draw.text((220, 1480), "OPTIONS", fill=RED, font=font(40))
            draw.text((700, 1480), "EXCUSES", fill=(70, 70, 70), font=font(40))

    elif combat == "phone_smash":
        draw_stick_params(draw, 480 + sx, hip_y, op_params, 1.38, WHITE, accent=True)
        # phone
        py = 880 - int(220 * ease_out_cubic(min(1.0, t * 1.4)))
        px = 720 + int(sx)
        draw.rounded_rectangle([px, py, px + 78, py + 130], radius=10, outline=GRAY, width=4)
        draw.rectangle([px + 18, py + 20, px + 60, py + 90], fill=(30, 30, 35))
        if t > 0.45:
            draw.line([px, py, px + 78, py + 130], fill=RED, width=5)
            draw.line([px + 78, py, px, py + 130], fill=RED, width=5)
            if impact_strength > 0.2:
                draw_impact_burst(draw, px + 40, py + 60, impact_strength)

    elif combat == "stance":
        draw_stick_params(draw, 540 + sx, hip_y, op_params, 1.42, WHITE, accent=True)
        # scanning arc
        ang = int(200 + 140 * ((math.sin(t * math.pi * 4) + 1) / 2))
        draw.arc([160 + sx, 620 + sy, 920 + sx, 1360 + sy], 200, ang, fill=RED, width=4)
        draw.ellipse([520 + sx, 980 + sy, 560 + sx, 1020 + sy], outline=RED, width=2)

    elif combat == "bleed":
        draw_stick_params(draw, 540 + sx, hip_y, op_params, 1.35, WHITE, accent=True)
        drops = int(1 + t * 6)
        for i in range(drops):
            dx = 200 + i * 90
            dy = 1460 + int(8 * math.sin(t * 20 + i))
            draw.ellipse([dx, dy, dx + 28, dy + 34], fill=(120, 18, 28))

    elif combat == "train":
        draw_stick_params(draw, 540 + sx, hip_y, op_params, 1.4, WHITE, accent=True)
        # training ghost target
        draw.ellipse([700 + sx, 900 + sy, 860 + sx, 1060 + sy], outline=(50, 50, 55), width=3)
        if impact_strength > 0.2:
            draw_impact_burst(draw, int(780 + sx), int(980 + sy), impact_strength)

    elif combat == "alone":
        draw_stick_params(draw, 540 + sx, hip_y, op_params, 1.45, WHITE, accent=True)
        # empty silhouettes faded
        for ox in (180, 900):
            draw_stick_params(draw, ox + sx * 0.3, hip_y, POSES["idle"], 0.9, (28, 28, 32), accent=False)

    elif combat == "oath":
        draw_stick_params(draw, 540 + sx, hip_y, op_params, 1.42, WHITE, accent=True)
        box_pulse = 1.0 + 0.04 * math.sin(t * math.pi * 6)
        bw = int(260 * box_pulse)
        draw.rectangle([540 - bw, 520 + sy, 540 + bw, 610 + sy], outline=RED, width=4)
        draw.text((540 - 200, 545 + sy), "NON-NEGOTIABLE", fill=RED, font=font(42))

    else:
        draw_stick_params(draw, 540 + sx, hip_y, op_params, 1.35, WHITE, accent=True)

    # ground line
    draw.line([(80, 1410 + sy), (1000, 1410 + sy)], fill=(55, 55, 60), width=3)

    # kinetic caption
    cap, cap_col = caption_at(lesson["captions"], t)
    # slam scale on caption change
    slam = 1.0
    for a, b, text, _ in lesson["captions"]:
        if text == cap and abs(t - a) < 0.06:
            slam = 1.0 + (0.06 - abs(t - a)) * 4
            break
    fsize = int(64 * slam)
    fnt = font(fsize)
    # measure
    bbox = draw.textbbox((0, 0), cap, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (W - tw) // 2
    ty = 280
    # dark plate
    pad = 28
    draw.rounded_rectangle(
        [tx - pad, ty - 18, tx + tw + pad, ty + th + 22],
        radius=8,
        fill=(0, 0, 0),
    )
    # red underline accent
    draw.rectangle([tx - pad, ty + th + 18, tx + tw + pad, ty + th + 24], fill=RED)
    # text shadow
    draw.text((tx + 3, ty + 3), cap, fill=(20, 20, 20), font=fnt)
    draw.text((tx, ty), cap, fill=cap_col, font=fnt)

    # bottom watermark
    draw.text((40, H - 64), "THE TYRRELL CODEX", fill=(50, 50, 55), font=font(24))

    # flash overlay
    if flash > 0.02:
        overlay = Image.new("RGB", (W, H), WHITE if flash > 0.55 else RED)
        img = Image.blend(img, overlay, min(0.55, flash * 0.65))

    # vignette
    vig = Image.new("RGB", (W, H), (0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for i in range(12):
        alpha_box = i * 18
        vd.rectangle([alpha_box, alpha_box, W - alpha_box, H - alpha_box], outline=(0, 0, 0))
    img = Image.blend(img, vig, 0.22)

    # slight sharpen for crisp stick lines
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
    return img


def write_wav_sfx(path: Path, duration: float, hits: list[float], whooshes: list[float]) -> None:
    """Procedural hits + whooshes + low dark drone bed."""
    sr = 44100
    n = int(duration * sr)
    audio = np.zeros(n, dtype=np.float32)
    t = np.arange(n) / sr

    # dark pulse bed
    bed = 0.04 * np.sin(2 * np.pi * 55 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.5 * t))
    audio += bed.astype(np.float32)

    rng = np.random.default_rng(7)
    for ht in hits:
        i0 = int(ht * sr)
        length = int(0.12 * sr)
        if i0 >= n:
            continue
        env = np.linspace(1, 0, length) ** 2
        noise = rng.normal(0, 1, length).astype(np.float32) * env * 0.55
        click = np.sin(2 * np.pi * 180 * np.arange(length) / sr) * env * 0.35
        chunk = (noise + click.astype(np.float32))
        i1 = min(n, i0 + length)
        audio[i0:i1] += chunk[: i1 - i0]

    for wt in whooshes:
        i0 = int(wt * sr)
        length = int(0.22 * sr)
        if i0 >= n:
            continue
        env = np.sin(np.linspace(0, np.pi, length)) ** 1.5
        noise = rng.normal(0, 1, length).astype(np.float32)
        # band-ish whoosh via cumulative sum highpass fake
        who = np.cumsum(noise)
        who = who / (np.max(np.abs(who)) + 1e-6) * env * 0.22
        i1 = min(n, i0 + length)
        audio[i0:i1] += who[: i1 - i0]

    # soft sting at end
    i0 = max(0, n - int(0.4 * sr))
    sting = np.sin(2 * np.pi * 110 * np.arange(n - i0) / sr) * np.linspace(0.25, 0, n - i0)
    audio[i0:] += sting.astype(np.float32)

    audio = np.clip(audio, -1, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())


def probe_duration(path: Path) -> float:
    r = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 28.0


async def tts(text: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    # slightly faster, colder — more Shorts energy
    c = edge_tts.Communicate(text, voice="en-US-ChristopherNeural", rate="+3%", pitch="-8Hz")
    await c.save(str(out))


def fx_times(chart: list[dict], dur: float) -> tuple[list[float], list[float]]:
    hits, whooshes = [], []
    for beat in chart:
        mid = (beat["a"] + beat["b"]) / 2 * dur
        if beat["fx"] == "hit":
            hits.append(beat["a"] * dur + (beat["b"] - beat["a"]) * dur * 0.35)
        elif beat["fx"] in ("whoosh", "scan"):
            whooshes.append(mid)
        elif beat["fx"] == "sting":
            hits.append(beat["a"] * dur + 0.05)
    return hits, whooshes


def build_video(lesson: dict, voice: Path, out_mp4: Path) -> None:
    dur = probe_duration(voice)
    # clamp Shorts window
    dur = max(18.0, min(dur + 0.35, 36.0))
    total = int(dur * FPS)
    chart = choreography(lesson["combat"])
    hits, whooshes = fx_times(chart, dur)

    frame_dir = out_mp4.parent / f".v2_{lesson['id']}"
    if frame_dir.exists():
        for p in frame_dir.glob("*"):
            p.unlink()
    frame_dir.mkdir(parents=True, exist_ok=True)

    for i in range(total):
        t = i / max(1, total - 1)
        beat, local = active_beat(chart, t)
        shake = (0.0, 0.0)
        flash = 0.0
        if beat["fx"] == "hit":
            peak = ease_out_cubic(1.0 - abs(local - 0.35) * 2.8)
            shake = (math.sin(i * 2.7) * 14 * peak, math.cos(i * 3.1) * 10 * peak)
            flash = peak * 0.85
        elif beat["fx"] == "sting" and local < 0.25:
            flash = (1 - local / 0.25) * 0.4
            shake = (math.sin(i) * 4, 0)

        img = render_frame(lesson, t, shake, flash)
        img.save(frame_dir / f"f_{i:05d}.png", optimize=True)
        if i % 60 == 0:
            print(f"  {lesson['id']}  {i}/{total} ({100*i/total:.0f}%)")

    sfx = out_mp4.parent / f".sfx_{lesson['id']}.wav"
    write_wav_sfx(sfx, dur, hits, whooshes)

    # mix VO + SFX
    mixed = out_mp4.parent / f".mix_{lesson['id']}.m4a"
    mix_cmd = [
        FFMPEG, "-y",
        "-i", str(voice),
        "-i", str(sfx),
        "-filter_complex",
        "[0:a]volume=1.0[a0];[1:a]volume=0.45[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[a]",
        "-map", "[a]",
        "-c:a", "aac", "-b:a", "256k",
        str(mixed),
    ]
    r = subprocess.run(mix_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # fallback VO only
        mixed = voice

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    pattern = str(frame_dir / "f_%05d.png")
    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", pattern,
        "-i", str(mixed),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "16",
        "-profile:v", "high",
        "-c:a", "aac", "-b:a", "256k",
        "-shortest",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2500:])

    # cleanup
    for p in frame_dir.glob("*"):
        p.unlink()
    try:
        frame_dir.rmdir()
    except OSError:
        pass
    for extra in (sfx,):
        if extra.exists():
            extra.unlink()
    mix_path = out_mp4.parent / f".mix_{lesson['id']}.m4a"
    if mix_path.exists():
        mix_path.unlink()


def write_script(lesson: dict) -> Path:
    d = ROOT / "content_core" / "stickman_lessons" / "scripts"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{lesson['id']}.md"
    p.write_text(
        f"""# {lesson['id'].upper()} — {lesson['title']}

**Series:** Ferrum Doctrine Stickman Combat Lessons  
**Engine:** Stickman Forge V2 (cinematic)  
**Length:** ~22–32s · Vertical 9:16 @ 30fps  
**Brand sting:** Ferrum

## HOOK
{lesson['hook']}

## LESSON (canon)
{lesson['body']}

## DEMAND
{lesson['demand']}

## VIRAL VO (rendered)
{lesson['vo']}

## CAPTIONS
{chr(10).join(f"- {a:.0%}–{b:.0%}: {text}" for a,b,text,_ in lesson['captions'])}
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
        "Ferrum Doctrine — cinematic stickman combat lessons.\n"
        "Channel: The Tyrrell Codex\n\n"
        "#FerrumDoctrine #Discipline #Stickman #StickmanFight #Masculinity "
        "#SelfMastery #HardTruths #Mindset #Shorts #Reels\n"
    )
    tags = [
        "ferrum doctrine", "stickman", "stickman fight", "discipline",
        "self mastery", "hard truths for men", "masculinity", "stoicism",
        "frame control", "anti comfort", "youtube shorts",
    ]
    for plat, folder in [
        ("youtube", ROOT / "platforms" / "youtube_shorts" / lesson["id"]),
        ("instagram", ROOT / "platforms" / "instagram_reels" / lesson["id"]),
        ("tiktok", ROOT / "platforms" / "tiktok" / "stickman" / lesson["id"]),
    ]:
        folder.mkdir(parents=True, exist_ok=True)
        man = {
            "platform": plat if plat != "youtube" else "youtube_shorts",
            "content_id": f"stickman-{lesson['id']}",
            "series": "Ferrum Doctrine Stickman Combat Lessons",
            "engine": "stickman_forge_v2",
            "file": video_rel,
            "title": title,
            "description": desc,
            "tags": tags,
            "thumbnail": None,
            "schedule": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "review",
            "quality_bar": "v2_cinematic_viral_benchmark",
            "pinned_comment": "You either do the demand or stay weak. Decide. The Tyrrell Codex / Ferrum Doctrine.",
            "monetization": {"midroll": False, "affiliate_links": [], "pinned_comment": "Decide. Or stay weak."},
        }
        (folder / "publish_manifest.json").write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
        (folder / "WHAT_WHERE_WHEN.md").write_text(
            f"# {lesson['title']}\n\n- WHAT: Stickman Forge V2 cinematic MP4\n"
            f"- WHERE: {plat}\n- WHEN: {man['schedule']}\n"
            f"- FILE: {video_rel}\n- ENGINE: v2\n",
            encoding="utf-8",
        )


def process_one(lesson: dict, day0: datetime) -> dict:
    print(f"=== V2 {lesson['id']} {lesson['title']} ===")
    write_script(lesson)
    voice = ROOT / "assets" / "voice" / "stickman" / f"{lesson['id']}_voice_v2.mp3"
    asyncio.run(tts(lesson["vo"], voice))
    out = ROOT / "assets" / "final" / "stickman" / f"{lesson['id']}.mp4"
    # archive prior low-quality if present
    legacy = ROOT / "assets" / "final" / "stickman" / f"{lesson['id']}_v1_legacy.mp4"
    if out.exists() and not legacy.exists():
        try:
            out.replace(legacy)
        except OSError:
            pass
    build_video(lesson, voice, out)
    rel = f"assets/final/stickman/{lesson['id']}.mp4"
    write_manifests(lesson, rel, int(lesson["id"].split("_")[1]) - 1, day0)
    size = out.stat().st_size if out.exists() else 0
    print(f"  DONE {rel} ({size/1024:.0f} KB)")
    return {
        "id": lesson["id"],
        "title": lesson["title"],
        "file": rel,
        "bytes": size,
        "engine": "v2",
    }


def main() -> None:
    import sys

    day0 = datetime(2026, 7, 19, 16, 0, 0, tzinfo=timezone.utc)
    only = None
    if len(sys.argv) > 1:
        only = sys.argv[1]  # e.g. lesson_01

    results = []
    for lesson in LESSONS:
        if only and lesson["id"] != only:
            continue
        results.append(process_one(lesson, day0))

    if only:
        # merge into index
        idx_path = ROOT / "content_core" / "stickman_lessons" / "CYCLE_001_INDEX.json"
        if idx_path.exists():
            index = json.loads(idx_path.read_text(encoding="utf-8"))
            by_id = {x["id"]: x for x in index.get("lessons", [])}
            for r in results:
                by_id[r["id"]] = r
            index["lessons"] = [by_id[L["id"]] for L in LESSONS if L["id"] in by_id]
            index["engine"] = "stickman_forge_v2"
            index["generated_at"] = datetime.now(timezone.utc).isoformat()
            index["status"] = "review"
            index["note"] = (
                "V2 cinematic re-render vs viral stickman Shorts benchmark. "
                "Authoritas review before Publicator upload. "
                "Higgsfield Seedance path blocked until hf auth login."
            )
            idx_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(results, indent=2))
        return

    index = {
        "cycle": "stickman_forge_cycle_001",
        "series": "Ferrum Doctrine Stickman Combat Lessons",
        "channel": "The Tyrrell Codex",
        "engine": "stickman_forge_v2",
        "count": len(results),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lessons": results,
        "status": "review",
        "quality_bar": {
            "benchmark": "viral stickman fight Shorts / Reels (impact frames, shake, kinetic type, SFX)",
            "fps": FPS,
            "resolution": f"{W}x{H}",
            "crf": 16,
            "vs_v1": "replaced static 4-hold slideshow with interpolated combat + FX",
        },
        "note": (
            "V2 cinematic re-render complete. Authoritas review then Publicator. "
            "Higgsfield Seedance/Nano Banana upgrade path available after: higgsfield auth login"
        ),
    }
    out_idx = ROOT / "content_core" / "stickman_lessons" / "CYCLE_001_INDEX.json"
    out_idx.parent.mkdir(parents=True, exist_ok=True)
    out_idx.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
