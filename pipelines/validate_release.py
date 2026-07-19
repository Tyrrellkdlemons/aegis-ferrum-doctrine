from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("youtube", "instagram", "tiktok", "x", "reddit")
REQUIRED_MANIFEST_KEYS = {
    "platform",
    "content_id",
    "file",
    "title",
    "description",
    "tags",
    "thumbnail",
    "schedule",
    "monetization",
}
READY_STATUSES = {"ready_local_not_published", "ready_text_not_published"}
REVIEW_STATUSES = {
    "review_rules_before_posting",
    "qa_hold",
    "script_complete_media_rework",
    "outline_complete_media_rework",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def body_word_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"## BODY\s+(.*?)\s+## CTA", text, flags=re.DOTALL)
    if not match:
        return 0
    return len(re.findall(r"\b[\w’'-]+\b", match.group(1), flags=re.UNICODE))


def probe_media(path: Path) -> dict:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        try:
            import imageio_ffmpeg

            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError as exc:
            raise FileNotFoundError("ffmpeg is unavailable") from exc

    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    metadata = result.stderr
    duration_match = re.search(
        r"Duration:\s*(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", metadata
    )
    if not duration_match:
        raise ValueError("duration metadata missing")
    hours, minutes, seconds = duration_match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    streams = []
    if re.search(r"Stream #.*Video:", metadata):
        streams.append({"codec_type": "video"})
    if re.search(r"Stream #.*Audio:", metadata):
        streams.append({"codec_type": "audio"})
    return {"format": {"duration": str(duration)}, "streams": streams}


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []

    for relative in (
        Path("content_core"),
        Path("platforms"),
        Path("dashboard"),
        Path("docs"),
    ):
        if not (ROOT / relative).is_dir():
            errors.append(f"missing directory: {relative}")

    for script in (
        Path("content_core/master_script.md"),
        Path("content_core/future/soft_habits_kill_ambition.md"),
    ):
        count = body_word_count(ROOT / script)
        if not 800 <= count <= 1200:
            errors.append(f"{script}: BODY is {count} words; expected 800-1200")
        else:
            notes.append(f"{script}: BODY {count} words")

    for platform in PLATFORMS:
        manifest_path = ROOT / "platforms" / platform / "publish_manifest.json"
        if not manifest_path.is_file():
            errors.append(f"missing manifest: {manifest_path.relative_to(ROOT)}")
            continue

        manifest = load_json(manifest_path)
        missing = REQUIRED_MANIFEST_KEYS - manifest.keys()
        if missing:
            errors.append(
                f"{manifest_path.relative_to(ROOT)} missing keys: {sorted(missing)}"
            )
        if manifest.get("platform") != platform:
            errors.append(f"{manifest_path.relative_to(ROOT)} platform mismatch")
        if not isinstance(manifest.get("tags"), list):
            errors.append(f"{manifest_path.relative_to(ROOT)} tags must be an array")

        try:
            datetime.fromisoformat(manifest["schedule"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            errors.append(f"{manifest_path.relative_to(ROOT)} has invalid schedule")

        asset = manifest_path.parent / str(manifest.get("file", ""))
        if not asset.is_file() or asset.stat().st_size == 0:
            errors.append(f"missing or empty release file: {asset.relative_to(ROOT)}")
        elif asset.suffix.lower() == ".mp4":
            try:
                probe = probe_media(asset)
                streams = probe.get("streams", [])
                kinds = {stream.get("codec_type") for stream in streams}
                if not {"video", "audio"} <= kinds:
                    errors.append(f"{asset.relative_to(ROOT)} lacks audio or video")
                duration = float(probe["format"]["duration"])
                notes.append(
                    f"{asset.relative_to(ROOT)}: {duration:.2f}s, "
                    f"{asset.stat().st_size:,} bytes"
                )
            except (KeyError, ValueError, subprocess.CalledProcessError) as exc:
                errors.append(f"ffprobe failed for {asset.relative_to(ROOT)}: {exc}")

        thumbnail = manifest.get("thumbnail")
        if thumbnail:
            thumbnail_path = manifest_path.parent / str(thumbnail)
            if not thumbnail_path.is_file() or thumbnail_path.stat().st_size == 0:
                errors.append(
                    f"missing or empty thumbnail: {thumbnail_path.relative_to(ROOT)}"
                )

        if manifest.get("status") == "published" and not manifest.get("publish_url"):
            errors.append(
                f"{manifest_path.relative_to(ROOT)} claims published without URL"
            )

    expected_long_hash = load_json(ROOT / "publish_clearance.json")["evidence"][
        "long_form_sha256"
    ]
    actual_long_hash = sha256(ROOT / "platforms/youtube/final_long.mp4")
    if expected_long_hash != actual_long_hash:
        errors.append("YouTube long-form SHA-256 does not match publish_clearance.json")
    else:
        notes.append(f"YouTube long-form SHA-256: {actual_long_hash}")

    for name in ("index.html", "app.js", "styles.css", "data/schedule.json"):
        source = ROOT / "dashboard" / name
        deployed = ROOT / "docs" / name
        if source.read_bytes() != deployed.read_bytes():
            errors.append(f"dashboard/docs drift: {name}")

    public_text = "\n".join(
        (ROOT / "docs" / name).read_text(encoding="utf-8-sig")
        for name in ("index.html", "app.js", "data/schedule.json")
    )
    if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", public_text):
        errors.append("public dashboard contains an email address")

    schedule = load_json(ROOT / "dashboard/data/schedule.json")
    posts = schedule.get("posts", [])
    computed = {
        "ready": sum(post.get("status") in READY_STATUSES for post in posts),
        "review": sum(post.get("status") in REVIEW_STATUSES for post in posts),
        "published": sum(post.get("status") == "published" for post in posts),
    }
    if schedule.get("summary") != computed:
        errors.append(
            f"dashboard summary mismatch: declared {schedule.get('summary')}, "
            f"computed {computed}"
        )

    performance = schedule.get("performance", {})
    for key in (
        "views_24h",
        "ctr_percent",
        "average_retention_percent",
        "subscriber_delta",
        "revenue_usd",
    ):
        if performance.get(key) is not None:
            errors.append(f"unverified performance metric is not null: {key}")

    for note in notes:
        print(f"PASS  {note}")
    for error in errors:
        print(f"FAIL  {error}", file=sys.stderr)

    if errors:
        print(f"\nRelease validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print("\nRelease validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
