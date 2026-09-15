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
import os
import shutil
import subprocess
import sys
import tempfile
import winreg
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "assets" / "remotion-template"
GATE = SKILL_DIR / "scripts" / "video_quality_gate.py"
VISUAL_GATE = SKILL_DIR / "scripts" / "video_visual_qa.py"
STORYBOARD_GATE = SKILL_DIR / "scripts" / "storyboard_gate.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_lock_semantic_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def execute(command: list[str], cwd: Path | None = None, timeout: int = 1200, env: dict[str, str] | None = None) -> int:
    resolved = shutil.which(command[0]) or command[0]
    if Path(resolved).suffix.lower() in {".cmd", ".bat"}:
        encoded = subprocess.list2cmdline([resolved, *command[1:]])
        return subprocess.run(encoded, cwd=str(cwd) if cwd else None, check=False, timeout=timeout, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"), env=env).returncode
    return subprocess.run([resolved, *command[1:]], cwd=str(cwd) if cwd else None, check=False, timeout=timeout, env=env).returncode


def wininet_proxy() -> str | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
            enabled = int(winreg.QueryValueEx(key, "ProxyEnable")[0])
            raw = str(winreg.QueryValueEx(key, "ProxyServer")[0])
    except OSError:
        return None
    if not enabled or not raw:
        return None
    if ";" in raw:
        pairs = dict(item.split("=", 1) for item in raw.split(";") if "=" in item)
        raw = pairs.get("https") or pairs.get("http") or ""
    if not raw:
        return None
    return raw if "://" in raw else f"http://{raw}"


def cmd_info() -> int:
    result = {"status": "PASS", "skill": str(SKILL_DIR), "template": str(TEMPLATE), "fixed_entry": str(Path(__file__).resolve()), "dependencies": {name: shutil.which(name) for name in ("node", "npm", "ffmpeg", "ffprobe")}}
    result["status"] = "PASS" if all(result["dependencies"].values()) else "FAIL"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


def cmd_create(project: Path) -> int:
    if project.exists() and any(project.iterdir()):
        print(json.dumps({"status": "FAIL", "error": "project_directory_not_empty", "project": str(project.resolve())}, ensure_ascii=False, indent=2)); return 2
    project.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE, project, dirs_exist_ok=True)
    if execute(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund", "--prefer-offline"], project, 600) != 0:
        return 2
    print(json.dumps({"status": "PASS", "project": str(project.resolve()), "package_lock_semantic_sha256": package_lock_semantic_sha256(project / "package-lock.json")}, ensure_ascii=False, indent=2))
    return 0


def cmd_voiceover(project: Path, input_file: Path, instructions: Path, voice: str, provider: str) -> int:
    speech_cli = SKILL_DIR.parent / "speech" / "scripts" / "text_to_speech.py"
    output = project / "public" / "voiceover.mp3"
    missing = [str(path) for path in (speech_cli, input_file, instructions) if not path.is_file()]
    if missing:
        print(json.dumps({"status": "FAIL", "errors": [f"missing:{item}" for item in missing]}, ensure_ascii=False, indent=2)); return 2
    environment = os.environ.copy()
    proxy = environment.get("HTTPS_PROXY") or wininet_proxy()
    if proxy:
        environment.setdefault("HTTPS_PROXY", proxy)
        environment.setdefault("HTTP_PROXY", proxy)
    code = 2
    actual_provider = "openai"
    if provider in {"auto", "openai"}:
        command = [sys.executable, str(speech_cli), "speak", "--input-file", str(input_file), "--instructions-file", str(instructions), "--voice", voice, "--response-format", "mp3", "--out", str(output), "--force"]
        code = execute(command, project, 300, environment)
    if code != 0 and provider in {"auto", "windows"}:
        actual_provider = "windows-sapi"
        helper = SKILL_DIR / "scripts" / "windows_sapi_tts.ps1"
        with tempfile.TemporaryDirectory(prefix="stock-recap-sapi-") as temp_dir:
            wave = Path(temp_dir) / "voiceover.wav"
            sapi = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(helper), "-InputFile", str(input_file), "-OutputFile", str(wave), "-Rate", "0"]
            code = execute(sapi, project, 120)
            if code == 0:
                voice_filter = "atempo=1.12,highpass=f=70,lowpass=f=10000,equalizer=f=180:t=q:w=1:g=1.5,acompressor=threshold=-18dB:ratio=2:attack=15:release=150:makeup=1.2"
                code = execute(["ffmpeg", "-y", "-i", str(wave), "-af", voice_filter, "-ar", "48000", "-ac", "1", "-b:a", "192k", str(output)], project, 120)
    result = {
        "schema": "stock-recap-voiceover-receipt.v1",
        "status": "PASS" if code == 0 and output.is_file() else "FAIL",
        "provider": actual_provider,
        "voice": voice if actual_provider == "openai" else "Microsoft Huihui Desktop",
        "input_script": str(input_file.resolve()),
        "script_sha256": sha256_file(input_file),
        "instructions_sha256": sha256_file(instructions),
        "voiceover": str(output.resolve()),
        "proxy_source": "environment" if os.environ.get("HTTPS_PROXY") else "wininet" if proxy else "none",
        "sha256": sha256_file(output) if output.is_file() else None,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt = project / "public" / "voiceover-receipt.json"
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["receipt"] = str(receipt.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


def cmd_render(project: Path, output: Path) -> int:
    metadata_path = project / "public" / "video-metadata.json"
    voiceover = project / "public" / "voiceover.mp3"
    captions = project / "public" / "captions.json"
    voiceover_receipt_path = project / "public" / "voiceover-receipt.json"
    storyboard_receipt_path = project / "public" / "storyboard-receipt.json"
    missing = [str(path) for path in (metadata_path, voiceover, captions, voiceover_receipt_path, storyboard_receipt_path) if not path.is_file()]
    if missing:
        print(json.dumps({"status": "FAIL", "errors": [f"missing:{item}" for item in missing]}, ensure_ascii=False, indent=2)); return 2
    if execute([sys.executable, str(STORYBOARD_GATE), "verify", "--project", str(project), "--receipt", str(storyboard_receipt_path)], timeout=120) != 0:
        return 2
    metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    voiceover_receipt = json.loads(voiceover_receipt_path.read_text(encoding="utf-8-sig"))
    storyboard_receipt = json.loads(storyboard_receipt_path.read_text(encoding="utf-8-sig"))
    captions_data = json.loads(captions.read_text(encoding="utf-8-sig"))
    evidence_sha = str(metadata.get("data_evidence_sha256") or "")
    trade_date = str(metadata.get("trade_date") or "")
    required_metadata = ("business_skill", "trade_date", "data_evidence_sha256", "script_sha256", "ai_voice_disclosure", "voice_provider", "source_cutoff")
    metadata_errors = [f"metadata_missing:{key}" for key in required_metadata if not str(metadata.get(key) or "").strip()]
    if len(evidence_sha) != 64 or any(value not in "0123456789abcdefABCDEF" for value in evidence_sha):
        metadata_errors.append("data_evidence_sha256_invalid")
    current_voice_sha = sha256_file(voiceover)
    if voiceover_receipt.get("status") != "PASS" or voiceover_receipt.get("sha256") != current_voice_sha:
        metadata_errors.append("voiceover_receipt_or_hash_mismatch")
    if metadata.get("script_sha256") != voiceover_receipt.get("script_sha256"):
        metadata_errors.append("metadata_script_sha256_mismatch")
    if metadata.get("voice_provider") != voiceover_receipt.get("provider"):
        metadata_errors.append("metadata_voice_provider_mismatch")
    if "AI" not in str(metadata.get("ai_voice_disclosure") or "").upper() and "人工智能" not in str(metadata.get("ai_voice_disclosure") or ""):
        metadata_errors.append("ai_voice_disclosure_invalid")
    if not isinstance(captions_data, list) or not captions_data:
        metadata_errors.append("captions_empty_or_not_list")
    else:
        previous_end = 0.0
        for index, item in enumerate(captions_data):
            text_value = str(item.get("text") or "") if isinstance(item, dict) else ""
            length = len("".join(text_value.split()))
            start = float(item.get("startMs") or 0) if isinstance(item, dict) else 0.0
            end = float(item.get("endMs") or 0) if isinstance(item, dict) else 0.0
            if not 4 <= length <= 20 or text_value.count("\n") > 1 or start < previous_end or end <= start:
                metadata_errors.append(f"caption_contract_invalid:{index}")
            previous_end = max(previous_end, end)
    if metadata_errors:
        print(json.dumps({"status": "FAIL", "errors": metadata_errors}, ensure_ascii=False, indent=2)); return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    proxy = environment.get("HTTPS_PROXY") or wininet_proxy()
    if proxy:
        environment.setdefault("HTTPS_PROXY", proxy)
        environment.setdefault("HTTP_PROXY", proxy)
    chrome_candidates = [Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"), Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")]
    chrome = next((item for item in chrome_candidates if item.is_file()), None)
    if chrome is None:
        print(json.dumps({"status": "FAIL", "errors": ["google_chrome_executable_missing"]}, ensure_ascii=False, indent=2)); return 2
    with tempfile.TemporaryDirectory(prefix="stock-recap-render-") as temp_dir:
        raw = Path(temp_dir) / "raw.mp4"
        if execute(["npx", "remotion", "render", "src/index.ts", "StockRecap", str(raw), "--codec=h264", "--pixel-format=yuv420p", "--audio-codec=aac", "--overwrite", f"--browser-executable={chrome}"], project, 1200, environment) != 0:
            return 2
        comment = (
            f"STOCK_DATA_TRADE_DATE={trade_date};DATA_EVIDENCE_SHA256={evidence_sha};"
            f"SCRIPT_SHA256={metadata['script_sha256']};VOICEOVER_SHA256={current_voice_sha};"
            f"CAPTIONS_SHA256={sha256_file(captions)};"
            f"STORYBOARD_SHA256={storyboard_receipt['storyboard_sha256']};"
            f"VOICE_PROVIDER={metadata['voice_provider']};SOURCE_CUTOFF={metadata['source_cutoff']};"
            f"{metadata['ai_voice_disclosure']};BUSINESS_SKILL={metadata['business_skill']}"
        )
        command = ["ffmpeg", "-y", "-i", str(raw), "-vf", "scale=in_range=pc:out_range=tv,format=yuv420p", "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1", "-preset", "medium", "-crf", "18", "-color_range", "tv", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-movflags", "+faststart", "-metadata", f"comment={comment}", str(output)]
        if execute(command, project, 600) != 0:
            return 2
    print(json.dumps({"status": "PASS", "video": str(output.resolve()), "sha256": sha256_file(output)}, ensure_ascii=False, indent=2))
    return 0


def cmd_selftest() -> int:
    errors = []
    warnings = []
    for required in (TEMPLATE / "package.json", TEMPLATE / "package-lock.json", TEMPLATE / "src" / "video.tsx", TEMPLATE / "public" / "captions.json", TEMPLATE / "public" / "storyboard.json", GATE, VISUAL_GATE, STORYBOARD_GATE, SKILL_DIR / "scripts" / "windows_sapi_transcribe.ps1"):
        if not required.is_file(): errors.append(f"missing:{required}")
    try:
        package = json.loads((TEMPLATE / "package.json").read_text(encoding="utf-8"))
        versions = {value for key, value in package.get("dependencies", {}).items() if key.startswith("@remotion/") or key == "remotion"}
        if len(versions) != 1: errors.append("remotion_versions_not_pinned_equal")
    except Exception as exc:
        errors.append(f"package_invalid:{type(exc).__name__}:{exc}")
    for name in ("node", "npm", "ffmpeg", "ffprobe"):
        if not shutil.which(name): errors.append(f"binary_missing:{name}")
    try:
        import cv2  # type: ignore  # noqa: F401
        import numpy  # type: ignore  # noqa: F401
    except Exception as exc:
        errors.append(f"visual_gate_python_dependency_missing:{type(exc).__name__}:{exc}")
    chrome_candidates = [Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"), Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")]
    if not any(path.is_file() for path in chrome_candidates): errors.append("google_chrome_executable_missing")
    for name, relative in (("speech", "scripts/text_to_speech.py"), ("transcribe", "scripts/transcribe_diarize.py")):
        path = SKILL_DIR.parent / name / relative
        if not path.is_file(): errors.append(f"installed_skill_entry_missing:{path}")
    sapi_check = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Speech; $s=[System.Speech.Synthesis.SpeechSynthesizer]::new(); try { if (@($s.GetInstalledVoices() | Where-Object {$_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'zh-CN'}).Count -lt 1) { exit 2 } } finally { $s.Dispose() }"],
        capture_output=True, text=True, timeout=60, check=False,
    )
    if sapi_check.returncode != 0: errors.append("windows_sapi_zh_cn_voice_missing")
    else:
        with tempfile.TemporaryDirectory(prefix="stock-recap-selftest-") as temp_dir:
            temp = Path(temp_dir)
            text_input = temp / "sapi-smoke.txt"
            wave_output = temp / "sapi-smoke.wav"
            text_input.write_text("语音自检通过。", encoding="utf-8")
            sapi_smoke = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SKILL_DIR / "scripts" / "windows_sapi_tts.ps1"), "-InputFile", str(text_input), "-OutputFile", str(wave_output)],
                capture_output=True, text=True, timeout=60, check=False,
            )
            if sapi_smoke.returncode != 0 or not wave_output.is_file() or wave_output.stat().st_size < 1000:
                errors.append("windows_sapi_synthesis_smoke_failed")
    recognizer_check = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Add-Type -AssemblyName System.Speech; if (@([System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | Where-Object {$_.Culture.Name -eq 'zh-CN'}).Count -lt 1) { exit 2 }"],
        capture_output=True, text=True, timeout=60, check=False,
    )
    if recognizer_check.returncode != 0: errors.append("windows_sapi_zh_cn_recognizer_missing")
    if not os.environ.get("OPENAI_API_KEY"): warnings.append("openai_cloud_voice_and_transcription_not_configured_local_sapi_fallback_available")
    else: warnings.append("openai_cloud_key_present_but_live_auth_not_tested_local_sapi_fallback_available")
    result = {"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings, "template": str(TEMPLATE)}
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if not errors else 2


def cmd_transcribe(project: Path, output: Path, dry_run: bool) -> int:
    voiceover = project / "public" / "voiceover.mp3"
    cli = SKILL_DIR.parent / "transcribe" / "scripts" / "transcribe_diarize.py"
    if not voiceover.is_file() or not cli.is_file():
        print(json.dumps({"status": "FAIL", "errors": ["voiceover_or_transcribe_cli_missing"]}, ensure_ascii=False, indent=2)); return 2
    environment = os.environ.copy()
    proxy = environment.get("HTTPS_PROXY") or wininet_proxy()
    if proxy:
        environment.setdefault("HTTPS_PROXY", proxy); environment.setdefault("HTTP_PROXY", proxy)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(cli), str(voiceover), "--language", "zh", "--response-format", "text", "--out", str(output)]
    if dry_run: command.append("--dry-run")
    code = execute(command, project, 600, environment)
    result = {"status": "PASS" if code == 0 else "FAIL", "mode": "dry-run" if dry_run else "live", "transcript": str(output.resolve()), "exists": output.is_file()}
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if code == 0 else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixed entry for polished stock recap video production")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info"); sub.add_parser("selftest")
    create = sub.add_parser("create"); create.add_argument("--project", required=True)
    voiceover = sub.add_parser("voiceover"); voiceover.add_argument("--project", required=True); voiceover.add_argument("--input", required=True); voiceover.add_argument("--instructions", required=True); voiceover.add_argument("--voice", default="cedar"); voiceover.add_argument("--provider", choices=("auto", "openai", "windows"), default="auto")
    render = sub.add_parser("render"); render.add_argument("--project", required=True); render.add_argument("--out", required=True)
    storyboard = sub.add_parser("storyboard"); storyboard.add_argument("--project", required=True); storyboard.add_argument("--receipt")
    verify_storyboard = sub.add_parser("verify-storyboard-receipt"); verify_storyboard.add_argument("--project", required=True); verify_storyboard.add_argument("--receipt")
    transcribe = sub.add_parser("transcribe"); transcribe.add_argument("--project", required=True); transcribe.add_argument("--out", required=True); transcribe.add_argument("--dry-run", action="store_true")
    visual = sub.add_parser("visual-qa"); visual.add_argument("--video", required=True); visual.add_argument("--out-dir", required=True); visual.add_argument("--receipt", required=True); visual.add_argument("--times")
    approve_visual = sub.add_parser("approve-visual"); approve_visual.add_argument("--receipt", required=True); approve_visual.add_argument("--scorecard", required=True); approve_visual.add_argument("--reviewed-by", required=True); approve_visual.add_argument("--confirm", required=True)
    verify_visual = sub.add_parser("verify-visual-receipt"); verify_visual.add_argument("--receipt", required=True)
    gate = sub.add_parser("gate"); gate.add_argument("--video", required=True); gate.add_argument("--script", required=True); gate.add_argument("--captions", required=True); gate.add_argument("--visual-receipt", required=True); gate.add_argument("--storyboard-receipt", required=True); gate.add_argument("--receipt", required=True); gate.add_argument("--min-duration", type=float, default=60.0); gate.add_argument("--max-duration", type=float, default=120.0)
    verify = sub.add_parser("verify-receipt"); verify.add_argument("--video", required=True); verify.add_argument("--receipt", required=True)
    args = parser.parse_args()
    if args.command == "info": return cmd_info()
    if args.command == "selftest": return cmd_selftest()
    if args.command == "create": return cmd_create(Path(args.project))
    if args.command == "voiceover": return cmd_voiceover(Path(args.project), Path(args.input), Path(args.instructions), args.voice, args.provider)
    if args.command == "render": return cmd_render(Path(args.project), Path(args.out))
    if args.command in {"storyboard", "verify-storyboard-receipt"}:
        receipt = Path(args.receipt).resolve() if args.receipt else Path(args.project).resolve() / "public" / "storyboard-receipt.json"
        action = "prepare" if args.command == "storyboard" else "verify"
        return execute([sys.executable, str(STORYBOARD_GATE), action, "--project", args.project, "--receipt", str(receipt)], timeout=120)
    if args.command == "transcribe": return cmd_transcribe(Path(args.project), Path(args.out), args.dry_run)
    if args.command == "visual-qa":
        command = [sys.executable, str(VISUAL_GATE), "prepare", "--video", args.video, "--out-dir", args.out_dir, "--receipt", args.receipt]
        if args.times: command += ["--times", args.times]
        return execute(command, timeout=600)
    if args.command == "approve-visual": return execute([sys.executable, str(VISUAL_GATE), "approve", "--receipt", args.receipt, "--scorecard", args.scorecard, "--reviewed-by", args.reviewed_by, "--confirm", args.confirm], timeout=120)
    if args.command == "verify-visual-receipt": return execute([sys.executable, str(VISUAL_GATE), "verify", "--receipt", args.receipt], timeout=120)
    command = [sys.executable, str(GATE), args.command, "--video", args.video, "--receipt", args.receipt]
    if args.command == "gate": command += ["--script", args.script, "--captions", args.captions, "--visual-receipt", args.visual_receipt, "--storyboard-receipt", args.storyboard_receipt, "--min-duration", str(args.min_duration), "--max-duration", str(args.max_duration)]
    return execute(command, timeout=600)


if __name__ == "__main__" and __import__("os").environ.get("ONESTOCK_STOCK_CANONICAL_CHILD") != "1":
    print("canonical_stock_legacy_entry_direct_execution_blocked", file=__import__("sys").stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
