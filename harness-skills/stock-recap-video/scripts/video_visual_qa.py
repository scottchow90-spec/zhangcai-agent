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
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

SCHEMA = "stock-recap-video-visual-qa.v3"
SCORECARD_SCHEMA = "stock-recap-aesthetic-scorecard.v2"
STATIC_THRESHOLD = 0.5
MAX_STATIC_PAIR_RATIO = 0.35
MIN_MEAN_DIFFERENCE = 0.55
MIN_LOWER_40_EDGE_RATIO = 0.018
MAX_LOWER_40_LOW_INFORMATION_ROW_RATIO = 0.65
REQUIRED_CONFIRMATIONS = [
    "all-scenes-sampled", "risk-notice-legible", "no-clipping", "no-overlap",
    "no-blank-scene", "caption-safe-area", "visual-hierarchy", "color-and-contrast",
]
SCORE_DIMENSIONS = [
    "composition", "typography", "color_depth", "motion", "data_visualization",
    "rhythm", "caption_integration", "brand_coherence",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duration_seconds(video: Path) -> float:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr[-400:] or "ffprobe failed")
    return float(json.loads(completed.stdout)["format"]["duration"])


def default_times(duration: float) -> list[float]:
    return [2.5, 8.0, 21.5, 37.5, 52.5, min(65.5, duration - 1.5)]


def scene_ranges(duration: float) -> list[tuple[str, float, float]]:
    if duration < 68:
        raise RuntimeError("fixed 70-second editorial timeline required")
    return [
        ("hook", 6.0, 14.8), ("breadth", 16.2, 28.6), ("themes", 30.0, 44.8),
        ("scenario", 46.2, 58.5), ("close", 60.2, min(68.5, duration - 0.8)),
    ]


def frame_at(capture: cv2.VideoCapture, second: float, color: bool = False) -> np.ndarray:
    capture.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
    ok, frame = capture.read()
    if not ok:
        raise RuntimeError(f"frame unavailable at {second}s")
    frame = cv2.resize(frame, (270, 480), interpolation=cv2.INTER_AREA)
    return frame if color else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def motion_metrics(video: Path, duration: float) -> dict:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError("opencv could not open video")
    scenes: list[dict] = []
    all_diffs: list[float] = []
    try:
        for name, start, end in scene_ranges(duration):
            seconds = np.arange(start, end + 0.001, 1.0).tolist()
            frames = [frame_at(capture, second) for second in seconds]
            diffs = [float(np.mean(cv2.absdiff(frames[index - 1], frames[index]))) for index in range(1, len(frames))]
            ratio = sum(value < STATIC_THRESHOLD for value in diffs) / max(1, len(diffs))
            all_diffs.extend(diffs)
            scenes.append({
                "name": name, "start": start, "end": end,
                "one_second_differences": [round(value, 4) for value in diffs],
                "static_pair_ratio": round(ratio, 4),
                "mean_difference": round(float(np.mean(diffs)) if diffs else 0.0, 4),
                "pass": ratio <= 0.60,
            })
    finally:
        capture.release()
    ratio = sum(value < STATIC_THRESHOLD for value in all_diffs) / max(1, len(all_diffs))
    mean = float(np.mean(all_diffs)) if all_diffs else 0.0
    passed = ratio <= MAX_STATIC_PAIR_RATIO and mean >= MIN_MEAN_DIFFERENCE and all(scene["pass"] for scene in scenes)
    return {
        "static_threshold": STATIC_THRESHOLD,
        "maximum_static_pair_ratio": MAX_STATIC_PAIR_RATIO,
        "minimum_mean_difference": MIN_MEAN_DIFFERENCE,
        "overall_static_pair_ratio": round(ratio, 4),
        "overall_mean_difference": round(mean, 4),
        "scene_ranges": scenes,
        "status": "PASS" if passed else "FAIL",
    }


def density_metrics(video: Path, times: list[float]) -> dict:
    business_times = [value for value in times if value >= 5.0]
    if len(business_times) < 5:
        raise RuntimeError("five business-scene density samples required")
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError("opencv could not open video for density analysis")
    samples: list[dict] = []
    try:
        for second in business_times:
            frame = frame_at(capture, second, color=True)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 45, 120)
            height = gray.shape[0]
            lower_edges = edges[int(height * 0.6):]
            row_edge_ratio = (edges > 0).mean(axis=1)
            lower_low_information_rows = row_edge_ratio[int(height * 0.6):] < 0.006
            samples.append({
                "second": round(second, 3),
                "lower_40_edge_ratio": round(float((lower_edges > 0).mean()), 4),
                "lower_40_low_information_row_ratio": round(float(lower_low_information_rows.mean()), 4),
            })
    finally:
        capture.release()
    mean_edge = float(np.mean([sample["lower_40_edge_ratio"] for sample in samples]))
    mean_low_information = float(np.mean([sample["lower_40_low_information_row_ratio"] for sample in samples]))
    passed = mean_edge >= MIN_LOWER_40_EDGE_RATIO and mean_low_information <= MAX_LOWER_40_LOW_INFORMATION_ROW_RATIO
    return {
        "minimum_mean_lower_40_edge_ratio": MIN_LOWER_40_EDGE_RATIO,
        "maximum_mean_lower_40_low_information_row_ratio": MAX_LOWER_40_LOW_INFORMATION_ROW_RATIO,
        "mean_lower_40_edge_ratio": round(mean_edge, 4),
        "mean_lower_40_low_information_row_ratio": round(mean_low_information, 4),
        "samples": samples,
        "status": "PASS" if passed else "FAIL",
    }


def scorecard_errors(path: Path, expected_video_sha: str) -> tuple[list[str], dict]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"scorecard_unreadable:{type(exc).__name__}:{exc}"], {}
    if data.get("schema") != SCORECARD_SCHEMA or data.get("video_sha256") != expected_video_sha:
        errors.append("scorecard_schema_or_video_binding_mismatch")
    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    for name in SCORE_DIMENSIONS:
        value = scores.get(name)
        if not isinstance(value, int) or not 8 <= value <= 10:
            errors.append(f"aesthetic_score_below_8_or_missing:{name}")
    if len(str(data.get("review_notes") or "").strip()) < 20:
        errors.append("review_notes_too_short")
    return errors, data


def verify_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    video = Path(str(payload.get("video") or ""))
    if payload.get("schema") != SCHEMA or payload.get("gate_sha256") != sha256_file(Path(__file__)):
        errors.append("visual_gate_version_or_hash_mismatch")
    if not video.is_file() or payload.get("video_sha256") != sha256_file(video):
        errors.append("video_missing_or_hash_mismatch")
    for item in payload.get("frames", []):
        frame = Path(str(item.get("path") or ""))
        if not frame.is_file() or item.get("sha256") != sha256_file(frame) or int(item.get("size_bytes") or -1) != frame.stat().st_size:
            errors.append(f"frame_missing_or_hash_mismatch:{frame}")
    contact_data = payload.get("contact_sheet") if isinstance(payload.get("contact_sheet"), dict) else {}
    contact = Path(str(contact_data.get("path") or ""))
    if not contact.is_file() or contact_data.get("sha256") != sha256_file(contact):
        errors.append("contact_sheet_missing_or_hash_mismatch")
    if payload.get("motion_metrics", {}).get("status") != "PASS":
        errors.append("within_scene_motion_gate_failed")
    if payload.get("visual_density", {}).get("status") != "PASS":
        errors.append("lower_frame_visual_density_gate_failed")
    if payload.get("status") == "PASS":
        if any(payload.get("checks", {}).get(name) is not True for name in REQUIRED_CONFIRMATIONS):
            errors.append("visual_confirmations_incomplete")
        if not str(payload.get("reviewed_by") or "").strip():
            errors.append("reviewer_missing")
        scorecard = Path(str(payload.get("scorecard", {}).get("path") or ""))
        if not scorecard.is_file() or payload.get("scorecard", {}).get("sha256") != sha256_file(scorecard):
            errors.append("scorecard_missing_or_hash_mismatch")
        else:
            score_errors, _ = scorecard_errors(scorecard, str(payload.get("video_sha256") or ""))
            errors.extend(score_errors)
    return errors


def cmd_prepare(args: argparse.Namespace) -> int:
    video = Path(args.video).resolve()
    receipt = Path(args.receipt).resolve()
    out_dir = Path(args.out_dir).resolve()
    if not video.is_file():
        print(json.dumps({"status": "FAIL", "errors": ["video_missing"]}, ensure_ascii=False, indent=2))
        return 2
    duration = duration_seconds(video)
    times = [float(value) for value in args.times.split(",")] if args.times else default_times(duration)
    if len(times) != 6 or any(value < 0 or value >= duration for value in times):
        print(json.dumps({"status": "FAIL", "errors": ["exactly_six_valid_sample_times_required"]}, ensure_ascii=False, indent=2))
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    frames: list[dict] = []
    images: list[np.ndarray] = []
    for index, second in enumerate(times, start=1):
        frame = out_dir / f"frame-{index:02d}.png"
        completed = subprocess.run(
            ["ffmpeg", "-y", "-ss", str(second), "-i", str(video), "-frames:v", "1", "-vf", "scale=540:960", str(frame)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, check=False,
        )
        if completed.returncode != 0 or not frame.is_file():
            print(json.dumps({"status": "FAIL", "errors": [f"frame_extract_failed:{second}"]}, ensure_ascii=False, indent=2))
            return 2
        image = cv2.imread(str(frame))
        if image is None:
            print(json.dumps({"status": "FAIL", "errors": [f"frame_unreadable:{frame}"]}, ensure_ascii=False, indent=2))
            return 2
        cv2.rectangle(image, (0, 0), (540, 48), (5, 14, 21), -1)
        cv2.putText(image, f"S{index}  {second:.1f}s", (18, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (230, 240, 244), 2, cv2.LINE_AA)
        images.append(image)
        frames.append({"second": round(second, 3), "path": str(frame), "sha256": sha256_file(frame), "size_bytes": frame.stat().st_size})
    row1 = cv2.hconcat(images[:3])
    row2 = cv2.hconcat(images[3:6])
    contact = out_dir / "contact-sheet.png"
    if not cv2.imwrite(str(contact), cv2.vconcat([row1, row2])):
        print(json.dumps({"status": "FAIL", "errors": ["contact_sheet_write_failed"]}, ensure_ascii=False, indent=2))
        return 2
    video_sha = sha256_file(video)
    scorecard = out_dir / "aesthetic-scorecard.json"
    scorecard.write_text(json.dumps({
        "schema": SCORECARD_SCHEMA,
        "video_sha256": video_sha,
        "scale": "8=internal-technical-prefilter, 9=strong, 10=exceptional; never proof of user-perceived polish",
        "scores": {name: None for name in SCORE_DIMENSIONS},
        "review_notes": "逐场景检查联系表与关键帧后填写；任一维度低于8即拒绝。用户明确否决时，无论分数多高都必须返工。",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    motion = motion_metrics(video, duration)
    density = density_metrics(video, times)
    preflight_passed = motion["status"] == "PASS" and density["status"] == "PASS"
    payload = {
        "schema": SCHEMA,
        "gate_sha256": sha256_file(Path(__file__)),
        "status": "REVIEW_REQUIRED" if preflight_passed else "FAIL",
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "video": str(video),
        "video_sha256": video_sha,
        "video_size_bytes": video.stat().st_size,
        "duration_seconds": duration,
        "sample_seconds": [round(value, 3) for value in times],
        "frames": frames,
        "contact_sheet": {"path": str(contact), "sha256": sha256_file(contact), "size_bytes": contact.stat().st_size},
        "motion_metrics": motion,
        "visual_density": density,
        "scorecard_template": str(scorecard),
        "checks": {name: False for name in REQUIRED_CONFIRMATIONS},
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "status": payload["status"], "receipt": str(receipt), "contact_sheet": str(contact),
        "scorecard": str(scorecard), "sample_count": len(frames),
        "motion_metrics": motion, "visual_density": density,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "REVIEW_REQUIRED" else 2


def cmd_approve(args: argparse.Namespace) -> int:
    receipt = Path(args.receipt).resolve()
    payload = json.loads(receipt.read_text(encoding="utf-8-sig"))
    confirmations = [item.strip() for item in args.confirm.split(",") if item.strip()]
    errors = verify_payload(payload)
    if confirmations != REQUIRED_CONFIRMATIONS:
        errors.append("exact_visual_confirmation_list_required")
    if not args.reviewed_by.strip():
        errors.append("reviewed_by_required")
    scorecard = Path(args.scorecard).resolve()
    score_errors, score_data = scorecard_errors(scorecard, str(payload.get("video_sha256") or ""))
    errors.extend(score_errors)
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, ensure_ascii=False, indent=2))
        return 2
    payload["status"] = "PASS"
    payload["checks"] = {name: True for name in REQUIRED_CONFIRMATIONS}
    payload["reviewed_by"] = args.reviewed_by.strip()
    payload["reviewed_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["scorecard"] = {
        "path": str(scorecard), "sha256": sha256_file(scorecard),
        "size_bytes": scorecard.stat().st_size, "scores": score_data["scores"],
    }
    receipt.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "receipt": str(receipt), "video_sha256": payload["video_sha256"], "scores": score_data["scores"]}, ensure_ascii=False, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    receipt = Path(args.receipt).resolve()
    try:
        payload = json.loads(receipt.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        result = {"status": "FAIL", "errors": [f"receipt_unreadable:{type(exc).__name__}:{exc}"]}
    else:
        errors = verify_payload(payload)
        if payload.get("status") != "PASS":
            errors.append("receipt_status_not_pass")
        result = {
            "status": "PASS" if not errors else "FAIL", "receipt": str(receipt),
            "video": payload.get("video"), "motion_metrics": payload.get("motion_metrics"),
            "visual_density": payload.get("visual_density"),
            "scores": payload.get("scorecard", {}).get("scores"), "errors": errors,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Visual technical prefilter for stock recap videos")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--video", required=True)
    prepare.add_argument("--out-dir", required=True)
    prepare.add_argument("--receipt", required=True)
    prepare.add_argument("--times")
    approve = sub.add_parser("approve")
    approve.add_argument("--receipt", required=True)
    approve.add_argument("--scorecard", required=True)
    approve.add_argument("--reviewed-by", required=True)
    approve.add_argument("--confirm", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--receipt", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        return cmd_prepare(args)
    if args.command == "approve":
        return cmd_approve(args)
    return cmd_verify(args)


if __name__ == "__main__":
    raise SystemExit(main())
