#!/usr/bin/env python3
from __future__ import annotations
# ONESTOCK_EMBEDDED_LOCAL_IMPORT_BOOTSTRAP
import sys as _onestock_embedded_sys
from pathlib import Path as _OneStockEmbeddedPath
_onestock_embedded_dir = str(_OneStockEmbeddedPath(__file__).resolve().parent)
if _onestock_embedded_dir not in _onestock_embedded_sys.path:
    _onestock_embedded_sys.path.insert(0, _onestock_embedded_dir)

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

GATE_VERSION = "stock-recap-video-gate.v3"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)


def ffprobe(path: Path) -> dict:
    completed = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr[-500:] or "ffprobe failed")
    return json.loads(completed.stdout)


def parse_rate(value: str) -> float:
    left, _, right = value.partition("/")
    return float(left) / float(right or 1)


def mp4_fast_start(path: Path) -> bool:
    """Return True when the top-level moov atom precedes mdat."""
    positions: dict[bytes, int] = {}
    with path.open("rb") as handle:
        while handle.tell() < path.stat().st_size:
            offset = handle.tell()
            header = handle.read(8)
            if len(header) != 8:
                break
            size = int.from_bytes(header[:4], "big")
            atom_type = header[4:8]
            header_size = 8
            if size == 1:
                extended = handle.read(8)
                if len(extended) != 8:
                    break
                size = int.from_bytes(extended, "big")
                header_size = 16
            elif size == 0:
                size = path.stat().st_size - offset
            if size < header_size:
                break
            positions.setdefault(atom_type, offset)
            if b"moov" in positions and b"mdat" in positions:
                break
            handle.seek(offset + size)
    return b"moov" in positions and b"mdat" in positions and positions[b"moov"] < positions[b"mdat"]


def detector(path: Path, filter_value: str) -> str:
    completed = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf", filter_value, "-an", "-f", "null", "-"], timeout=300)
    return completed.stderr


def audio_detector(path: Path, filter_value: str) -> str:
    completed = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", filter_value, "-vn", "-f", "null", "-"], timeout=300)
    return completed.stderr


def normalize_zh(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.lower())


def narration_readback(video: Path, script: Path) -> dict:
    helper = Path(__file__).with_name("windows_sapi_transcribe.ps1")
    with tempfile.TemporaryDirectory(prefix="stock-recap-asr-") as temp_dir:
        wave = Path(temp_dir) / "narration.wav"
        converted = run(["ffmpeg", "-y", "-i", str(video), "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wave)], timeout=300)
        if converted.returncode != 0 or not wave.is_file():
            raise RuntimeError(f"audio extraction failed: {converted.stderr[-400:]}")
        completed = run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(helper),
            "-WavePath", str(wave), "-ExpectedScript", str(script),
        ], timeout=300)
        if completed.returncode != 0:
            raise RuntimeError(f"Windows narration readback failed: {completed.stderr[-500:]}")
        payload = json.loads(completed.stdout)
    expected = [str(value) for value in payload.get("expected_phrases", [])]
    segments = [item for item in payload.get("segments", []) if isinstance(item, dict)]
    recognized = "".join(str(item.get("text", "")) for item in segments)
    matched = [phrase for phrase in expected if normalize_zh(phrase) in normalize_zh(recognized)]
    confidences = [float(item.get("confidence") or 0) for item in segments]
    minimum_confidence = min(confidences) if confidences else 0.0
    return {
        "status": "PASS" if expected and len(matched) == len(expected) and minimum_confidence >= 0.75 else "FAIL",
        "recognizer": payload.get("recognizer"),
        "expected_phrases": expected,
        "recognized_segments": segments,
        "matched_phrase_count": len(matched),
        "expected_phrase_count": len(expected),
        "minimum_confidence": round(minimum_confidence, 4),
    }


def captions_check(captions_path: Path, video_duration: float, metadata_text: str) -> dict:
    try:
        items = json.loads(captions_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "FAIL", "errors": [f"captions_unreadable:{type(exc).__name__}:{exc}"]}
    errors: list[str] = []
    previous_end = 0.0
    rows: list[dict] = []
    if not isinstance(items, list) or not items:
        errors.append("captions_empty_or_not_list")
        items = []
    for index, item in enumerate(items):
        text_value = str(item.get("text") or "") if isinstance(item, dict) else ""
        length = len(re.sub(r"\s+", "", text_value))
        start = float(item.get("startMs") or 0) if isinstance(item, dict) else 0.0
        end = float(item.get("endMs") or 0) if isinstance(item, dict) else 0.0
        row_errors = []
        if not 4 <= length <= 20: row_errors.append("length_out_of_range")
        if text_value.count("\n") > 1: row_errors.append("more_than_two_lines")
        if start < previous_end or end <= start: row_errors.append("timeline_overlap_or_invalid")
        if end > (video_duration - 5.0) * 1000 + 250: row_errors.append("timeline_exceeds_business_duration")
        rows.append({"index": index, "text": text_value, "normalized_length": length, "startMs": start, "endMs": end, "errors": row_errors})
        errors.extend(f"caption_{index}:{value}" for value in row_errors)
        previous_end = max(previous_end, end)
    captions_sha = sha256_file(captions_path) if captions_path.is_file() else ""
    if f"CAPTIONS_SHA256={captions_sha}" not in metadata_text:
        errors.append("captions_hash_not_embedded")
    return {"status": "PASS" if not errors else "FAIL", "path": str(captions_path.resolve()), "sha256": captions_sha, "count": len(rows), "rows": rows, "errors": errors}


def visual_receipt_check(video: Path, receipt: Path) -> dict:
    helper = Path(__file__).with_name("video_visual_qa.py")
    completed = run([sys.executable, str(helper), "verify", "--receipt", str(receipt)], timeout=120)
    errors: list[str] = []
    if completed.returncode != 0:
        errors.append("visual_receipt_verify_failed")
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        payload = {}
        errors.append(f"visual_receipt_unreadable:{type(exc).__name__}:{exc}")
    if payload.get("video_sha256") != sha256_file(video):
        errors.append("visual_receipt_video_hash_mismatch")
    return {
        "status": "PASS" if not errors else "FAIL",
        "receipt": str(receipt.resolve()),
        "reviewed_by": payload.get("reviewed_by"),
        "sample_count": len(payload.get("frames", [])),
        "errors": errors,
    }


def storyboard_receipt_check(receipt: Path, metadata_text: str) -> dict:
    helper = Path(__file__).with_name("storyboard_gate.py")
    errors: list[str] = []
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        payload = {}
        errors.append(f"storyboard_receipt_unreadable:{type(exc).__name__}:{exc}")
    project = Path(str(payload.get("project") or ""))
    if not project.is_dir():
        errors.append("storyboard_project_missing")
    else:
        completed = run([sys.executable, str(helper), "verify", "--project", str(project), "--receipt", str(receipt)], timeout=120)
        if completed.returncode != 0:
            errors.append("storyboard_receipt_verify_failed")
    storyboard_sha = str(payload.get("storyboard_sha256") or "")
    if not storyboard_sha or f"STORYBOARD_SHA256={storyboard_sha}" not in metadata_text:
        errors.append("storyboard_hash_not_embedded")
    return {"status": "PASS" if not errors else "FAIL", "receipt": str(receipt.resolve()), "storyboard_sha256": storyboard_sha, "errors": errors}


def frame_metrics(path: Path, duration: float) -> dict:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError("opencv could not open video")
    samples: list[dict] = []
    frames: list[np.ndarray] = []
    for second in sorted(set([0.5, 2.5, 4.5, 5.5, max(5.5, duration * 0.45), max(5.5, duration - 0.5)])):
        capture.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
        ok, frame = capture.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        samples.append({"second": round(second, 3), "mean_luma": round(float(gray.mean()), 3), "std_luma": round(float(gray.std()), 3)})
        frames.append(gray)
    capture.release()
    differences = [float(np.mean(cv2.absdiff(frames[index - 1], frames[index]))) for index in range(1, len(frames))]
    return {"samples": samples, "adjacent_mean_differences": [round(item, 3) for item in differences], "motion_ok": bool(differences and max(differences) >= 2.0), "frames_read": len(frames)}


def inspect(video: Path, script: Path, captions: Path, visual_receipt: Path, storyboard_receipt: Path, minimum_duration: float = 60.0, maximum_duration: float = 120.0) -> dict:
    result = {"status": "FAIL", "video": str(video.resolve()), "errors": [], "checks": {}}
    if not video.is_file():
        result["errors"].append("video_missing")
        return result
    result["sha256"] = sha256_file(video)
    result["size_bytes"] = video.stat().st_size
    try:
        probe = ffprobe(video)
    except Exception as exc:
        result["errors"].append(f"ffprobe_failed:{type(exc).__name__}:{exc}")
        return result
    streams = probe.get("streams", [])
    videos = [item for item in streams if item.get("codec_type") == "video"]
    audios = [item for item in streams if item.get("codec_type") == "audio"]
    duration = float(probe.get("format", {}).get("duration") or 0)
    video_stream = videos[0] if videos else {}
    audio_stream = audios[0] if audios else {}
    metadata_text = json.dumps(probe.get("format", {}).get("tags", {}), ensure_ascii=False)
    structure = {
        "video_stream": bool(videos), "audio_stream": bool(audios), "duration_seconds": duration,
        "duration_contract_seconds": [minimum_duration, maximum_duration],
        "duration_in_contract": minimum_duration <= duration <= maximum_duration,
        "width": video_stream.get("width"), "height": video_stream.get("height"), "fps": parse_rate(str(video_stream.get("avg_frame_rate", "0/1"))),
        "video_codec": video_stream.get("codec_name"), "pixel_format": video_stream.get("pix_fmt"),
        "audio_codec": audio_stream.get("codec_name"), "sample_rate": int(audio_stream.get("sample_rate") or 0),
        "fast_start": mp4_fast_start(video),
        "evidence_hash_embedded": bool(re.search(r"[0-9a-f]{64}", metadata_text, re.I)),
        "trade_date_marker_embedded": "STOCK_DATA_TRADE_DATE=" in metadata_text,
        "ai_voice_disclosure_embedded": "AI生成配音" in metadata_text,
    }
    result["checks"]["structure"] = structure
    if not all([structure["video_stream"], structure["audio_stream"], structure["duration_in_contract"], (structure["width"], structure["height"]) in {(1080, 1920), (1920, 1080)}, abs(structure["fps"] - 30) < 0.05, structure["video_codec"] == "h264", structure["pixel_format"] == "yuv420p", structure["audio_codec"] == "aac", structure["sample_rate"] == 48000, structure["fast_start"], structure["evidence_hash_embedded"], structure["trade_date_marker_embedded"], structure["ai_voice_disclosure_embedded"]]):
        result["errors"].append("media_structure_or_metadata_invalid")
    black = detector(video, "blackdetect=d=0.25:pix_th=0.10")
    freeze = detector(video, "freezedetect=n=-60dB:d=3")
    silence = audio_detector(video, "silencedetect=n=-45dB:d=2")
    loudness = audio_detector(video, "ebur128=peak=true")
    black_intervals = re.findall(r"black_start:([0-9.]+).*?black_end:([0-9.]+)", black)
    freeze_durations = [float(value) for value in re.findall(r"lavfi\.freezedetect\.freeze_duration: ([0-9.]+)", freeze)]
    silence_intervals = [(float(a), float(b)) for a, b in re.findall(r"silence_start: ([0-9.]+).*?silence_end: ([0-9.]+)", silence, re.S)]
    integrated = re.findall(r"I:\s+(-?[0-9.]+) LUFS", loudness)
    integrated_lufs = float(integrated[-1]) if integrated else math.nan
    result["checks"]["black_frames"] = {"intervals": black_intervals, "ok": not black_intervals}
    result["checks"]["freeze"] = {"durations": freeze_durations, "ok": not any(value >= 6 for value in freeze_durations)}
    risk_silence_ok = any(start <= 0.2 and end >= 4.8 for start, end in silence_intervals)
    unexpected_silence = [(start, end) for start, end in silence_intervals if start >= 5.2 and end - start >= 4]
    result["checks"]["audio"] = {"silence_intervals": silence_intervals, "risk_notice_silent": risk_silence_ok, "unexpected_silence": unexpected_silence, "integrated_lufs": integrated_lufs, "loudness_ok": not math.isnan(integrated_lufs) and -24 <= integrated_lufs <= -12}
    try:
        pixels = frame_metrics(video, duration)
    except Exception as exc:
        pixels = {"motion_ok": False, "error": f"{type(exc).__name__}:{exc}"}
    result["checks"]["pixels"] = pixels
    if black_intervals:
        result["errors"].append("black_frames_detected")
    if any(value >= 6 for value in freeze_durations):
        result["errors"].append("long_freeze_detected")
    if not risk_silence_ok:
        result["errors"].append("risk_notice_audio_not_silent")
    if unexpected_silence:
        result["errors"].append("unexpected_business_silence")
    if math.isnan(integrated_lufs) or not -24 <= integrated_lufs <= -12:
        result["errors"].append("integrated_loudness_out_of_range")
    if not pixels.get("motion_ok"):
        result["errors"].append("motion_not_confirmed")
    captions_result = captions_check(captions, duration, metadata_text)
    result["checks"]["captions"] = captions_result
    if captions_result.get("status") != "PASS":
        result["errors"].append("captions_contract_failed")
    visual_result = visual_receipt_check(video, visual_receipt)
    result["checks"]["visual_qa"] = visual_result
    if visual_result.get("status") != "PASS":
        result["errors"].append("visual_qa_receipt_failed")
    storyboard_result = storyboard_receipt_check(storyboard_receipt, metadata_text)
    result["checks"]["storyboard"] = storyboard_result
    if storyboard_result.get("status") != "PASS":
        result["errors"].append("storyboard_receipt_failed")
    if not script.is_file():
        result["errors"].append("script_missing")
    else:
        script_sha = sha256_file(script)
        result["checks"]["script"] = {
            "path": str(script.resolve()), "sha256": script_sha,
            "nonempty": bool(script.read_text(encoding="utf-8-sig").strip()),
            "hash_embedded": f"SCRIPT_SHA256={script_sha}" in metadata_text,
        }
        if not result["checks"]["script"]["nonempty"]:
            result["errors"].append("script_empty")
        if not result["checks"]["script"]["hash_embedded"]:
            result["errors"].append("script_hash_not_embedded")
        try:
            readback = narration_readback(video, script)
        except Exception as exc:
            readback = {"status": "FAIL", "error": f"{type(exc).__name__}:{exc}"}
        result["checks"]["narration_readback"] = readback
        if readback.get("status") != "PASS":
            result["errors"].append("narration_readback_mismatch")
    result["status"] = "PASS" if not result["errors"] else "FAIL"
    return result


def write_receipt(path: Path, result: dict) -> None:
    payload = {"schema": GATE_VERSION, "gate_sha256": sha256_file(Path(__file__)), "validated_at_utc": datetime.now(timezone.utc).isoformat(), **result}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def verify(video: Path, receipt: Path) -> dict:
    errors: list[str] = []
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "FAIL", "errors": [f"receipt_unreadable:{type(exc).__name__}:{exc}"]}
    if payload.get("status") != "PASS":
        errors.append("receipt_not_pass")
    if payload.get("schema") != GATE_VERSION or payload.get("gate_sha256") != sha256_file(Path(__file__)):
        errors.append("gate_version_or_hash_mismatch")
    if not video.is_file() or payload.get("sha256") != sha256_file(video):
        errors.append("video_hash_mismatch")
    return {"status": "PASS" if not errors else "FAIL", "video": str(video.resolve()), "receipt": str(receipt.resolve()), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    gate = sub.add_parser("gate"); gate.add_argument("--video", required=True); gate.add_argument("--script", required=True); gate.add_argument("--captions", required=True); gate.add_argument("--visual-receipt", required=True); gate.add_argument("--storyboard-receipt", required=True); gate.add_argument("--receipt", required=True); gate.add_argument("--min-duration", type=float, default=60.0); gate.add_argument("--max-duration", type=float, default=120.0)
    check = sub.add_parser("verify-receipt"); check.add_argument("--video", required=True); check.add_argument("--receipt", required=True)
    args = parser.parse_args()
    if args.command == "gate":
        result = inspect(Path(args.video), Path(args.script), Path(args.captions), Path(args.visual_receipt), Path(args.storyboard_receipt), args.min_duration, args.max_duration); write_receipt(Path(args.receipt), result)
    else:
        result = verify(Path(args.video), Path(args.receipt))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
