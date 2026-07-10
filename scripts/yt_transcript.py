#!/usr/bin/env python3
"""
yt_transcript.py — Transcript cho yt-content skill

Pipeline:
1) youtube-transcript-api — lấy captions/subtitles trực tiếp (FREE, nhanh, ổn định)
2) yt-dlp download → Deepgram STT (fallback khi video không có captions)

Usage:
  # Ưu tiên: YouTube URL → youtube-transcript-api → fallback Deepgram
  python3 scripts/yt_transcript.py --youtube-url "https://youtu.be/xxx" --output <tempdir>/transcript.txt --stats

  # Trực tiếp file audio/video local → Deepgram
  python3 scripts/yt_transcript.py --input <tempdir>/yt_audio.mp3 --output <tempdir>/transcript.txt --stats
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import NamedTuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===== Secrets/config =====
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SECRETS_FILE = WORKSPACE_ROOT / "credentials" / "yt_content_secrets.json"


def load_secrets() -> dict:
    if not SECRETS_FILE.exists():
        # Return fallback dummy values to prevent crash on startup
        # if only youtube-transcript-api is used.
        return {
            "deepgram_api_key": "dummy_key",
            "deepgram_url": "https://api.deepgram.com/v1/listen"
        }
    try:
        data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON secrets file: {e}")

    required = ["deepgram_api_key", "deepgram_url"]
    missing = [k for k in required if k not in data or not data[k]]
    if missing:
        raise RuntimeError(f"Missing required secrets keys: {', '.join(missing)}")
    return data


def get_runtime_config() -> dict:
    s = load_secrets()
    return {
        "DEEPGRAM_KEY": s["deepgram_api_key"],
        "DEEPGRAM_URL": s["deepgram_url"],
    }

_CFG = get_runtime_config()
DEEPGRAM_KEY = _CFG["DEEPGRAM_KEY"]
DEEPGRAM_URL = _CFG["DEEPGRAM_URL"]

DEFAULT_CHUNK_SIZE = 8000
DEFAULT_MAX_CHARS = 100000
DEFAULT_OUTPUT = str(Path(tempfile.gettempdir()) / "yt_transcript.txt")
REQUEST_TIMEOUT = 60
DEEPGRAM_TIMEOUT = 300

# Cookies file locations (for yt-dlp)
COOKIES_PERSISTENT = WORKSPACE_ROOT / "credentials" / "yt_cookies.txt"
COOKIES_TMP = Path(tempfile.gettempdir()) / "yt_cookies.txt"

# Transcript cache
CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache"
CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 ngày

# Error codes for classification
ERROR_CODES = {
    "invalid_url": "Invalid YouTube URL format",
    "no_captions": "Video has no captions/subtitles available",
    "network_timeout": "Network timeout",
    "empty_transcript": "Transcript is empty or placeholder-only",
    "provider_schema_error": "Unexpected response schema from provider",
    "file_not_found": "Input file not found",
    "download_failed": "Audio download failed",
    "unknown": "Unknown error",
}

# Placeholder patterns to detect non-meaningful transcript content
PLACEHOLDER_PATTERNS = [
    r'^\s*\[.*?\]\s*$',   # [MUSIC], [APPLAUSE], etc.
    r'^\s*\(.*?\)\s*$',   # (music playing), etc.
    r'^\s*♪.*♪\s*$',      # ♪ music notes ♪
]
PLACEHOLDER_REGEX = re.compile('|'.join(PLACEHOLDER_PATTERNS), re.IGNORECASE | re.MULTILINE)

# Quality thresholds
MIN_MEANINGFUL_CHARS = 50
MIN_MEANINGFUL_LINE_RATIO = 0.3


# =============================================================================
# Cache helpers
# =============================================================================

def _cache_key(video_id: str, lang_policy: str) -> str:
    """Unique cache key from video_id + lang policy."""
    return f"{video_id}__{lang_policy}"


def get_cache_path(video_id: str, lang_policy: str) -> Path:
    """Trả về path file cache cho video + lang."""
    return CACHE_DIR / f"{_cache_key(video_id, lang_policy)}.txt"


def load_from_cache(video_id: str, lang_policy: str) -> str | None:
    """
    Load transcript từ cache nếu tồn tại và chưa hết TTL.
    Cache file format: dòng 1 = '#ts:<unix_timestamp>', phần còn lại là transcript.
    Trả None nếu miss, expired, hoặc corrupt.
    """
    cache_path = get_cache_path(video_id, lang_policy)
    if not cache_path.exists():
        return None
    try:
        content = cache_path.read_text(encoding="utf-8")
        lines = content.split("\n", 1)
        if len(lines) < 2 or not lines[0].startswith("#ts:"):
            return None
        ts = float(lines[0][4:])
        if time.time() - ts > CACHE_TTL_SECONDS:
            cache_path.unlink(missing_ok=True)
            return None
        return lines[1] if lines[1].strip() else None
    except Exception:
        return None


def save_to_cache(video_id: str, lang_policy: str, transcript: str) -> None:
    """Lưu transcript vào cache với timestamp header."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = get_cache_path(video_id, lang_policy)
        cache_path.write_text(f"#ts:{time.time()}\n{transcript}", encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Cache write failed: {e}", file=sys.stderr)


# =============================================================================
# po_token / yt-dlp-get-pot detection
# =============================================================================

def detect_pot_provider() -> bool:
    """
    Kiểm tra yt-dlp-get-pot plugin có installed không.
    Dùng python -c import để tránh side-effects.
    Returns True nếu plugin available.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import yt_dlp_get_pot; print('ok')"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0 and "ok" in result.stdout
    except Exception:
        return False


class TranscriptError(Exception):
    """Custom exception with error classification."""
    def __init__(self, message: str, error_code: str, provider: str = "unknown", attempts: list = None):
        super().__init__(message)
        self.error_code = error_code
        self.provider = provider
        self.message = message
        self.attempts = attempts or []


class TranscriptResult(NamedTuple):
    """Result from transcript fetch."""
    transcript: str
    provider: str
    provider_attempts: list
    quality_checks: dict


def create_session_with_retry(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
) -> requests.Session:
    """Create a requests session with retry/backoff for transient errors."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def classify_http_error(status_code: int) -> str:
    """Classify HTTP error into error code."""
    if status_code == 401:
        return "auth_error"
    if status_code in (402, 403):
        return "forbidden"
    if status_code == 429:
        return "rate_limit"
    if status_code in (500, 502, 503, 504):
        return "network_timeout"
    return "unknown"


def validate_transcript_quality(transcript: str) -> dict:
    """
    Validate transcript quality.
    Returns dict with quality metrics and pass/fail status.
    """
    if not transcript or not transcript.strip():
        return {
            "passed": False,
            "reason": "empty",
            "char_count": 0,
            "meaningful_chars": 0,
            "total_lines": 0,
            "meaningful_lines": 0,
            "meaningful_line_ratio": 0.0,
        }

    lines = [l.strip() for l in transcript.strip().split('\n') if l.strip()]
    total_lines = len(lines)

    meaningful_lines = []
    placeholder_lines = []
    for line in lines:
        if PLACEHOLDER_REGEX.fullmatch(line):
            placeholder_lines.append(line)
        else:
            meaningful_lines.append(line)

    meaningful_line_count = len(meaningful_lines)
    meaningful_text = ' '.join(meaningful_lines)
    meaningful_chars = len(meaningful_text)

    meaningful_ratio = meaningful_line_count / total_lines if total_lines > 0 else 0.0

    passed = True
    reason = "ok"

    if meaningful_chars < MIN_MEANINGFUL_CHARS:
        passed = False
        reason = f"insufficient_chars ({meaningful_chars} < {MIN_MEANINGFUL_CHARS})"
    elif meaningful_ratio < MIN_MEANINGFUL_LINE_RATIO:
        passed = False
        reason = f"too_many_placeholders (ratio {meaningful_ratio:.2f} < {MIN_MEANINGFUL_LINE_RATIO})"

    return {
        "passed": passed,
        "reason": reason,
        "char_count": len(transcript),
        "meaningful_chars": meaningful_chars,
        "total_lines": total_lines,
        "meaningful_lines": meaningful_line_count,
        "meaningful_line_ratio": round(meaningful_ratio, 3),
    }


def extract_video_id(url: str) -> str | None:
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([^&\n?#]+)',
        r'youtube\.com\/shorts\/([^&\n?#]+)'
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def chunk_text(text: str, chunk_size: int) -> list[str]:
    """Split text into chunks, ưu tiên ngắt theo câu."""
    if chunk_size <= 0 or len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break

        best_break = -1
        search_start = max(start, end - 500)
        for i in range(end, search_start, -1):
            if text[i] in '.!?\n':
                best_break = i + 1
                break

        if best_break > start:
            chunks.append(text[start:best_break])
            start = best_break
        else:
            space_pos = text.rfind(' ', search_start, end)
            if space_pos > start:
                chunks.append(text[start:space_pos])
                start = space_pos + 1
            else:
                chunks.append(text[start:end])
                start = end

    return chunks


# =============================================================================
# Layer 1: youtube-transcript-api (PRIMARY — FREE, nhanh, ổn định)
# =============================================================================

def rank_transcript(transcript_info, target_lang: str = "vi") -> int:
    """
    Trả về score ưu tiên cho một transcript item.
    Score cao hơn = ưu tiên hơn.

    Priority order (for Vietnamese Shorts content):
      100 — manual, language starts with target_lang (e.g. vi)
       80 — generated, language starts with target_lang (e.g. a.vi, vi-VR, vi-Hans)
       60 — generated, language is exact target_lang variant not already matched
       40 — manual, language starts with 'en'
       20 — generated, language starts with 'en'
       10 — anything else (manual)
        5 — anything else (generated)
    """
    lc = (transcript_info.language_code or "").lower()
    is_gen = getattr(transcript_info, "is_generated", False)
    tgt = target_lang.lower()

    if not is_gen and lc.startswith(tgt):
        return 100
    if is_gen and (lc.startswith(tgt) or lc.startswith(f"a.{tgt}")):
        return 80
    if is_gen and tgt in lc:
        return 60
    if not is_gen and lc.startswith("en"):
        return 40
    if is_gen and lc.startswith("en"):
        return 20
    if not is_gen:
        return 10
    return 5


# =============================================================================
# Layer 1: youtube-transcript-api (PRIMARY — FREE, nhanh, ổn định)
# =============================================================================

def fetch_youtube_captions(video_id: str, lang: str = "vi") -> tuple[str, list]:
    """
    Lấy captions/subtitles trực tiếp từ YouTube API (v0.7+).
    Không cần download audio, không cần API key.

    Chiến lược list()-first:
    1. Discover TẤT CẢ available transcripts qua list()
    2. Rank theo priority (manual vi > generated a.vi/vi-VR > manual en > ...)
    3. Fetch theo thứ tự tốt nhất → dừng khi quality check pass

    Returns: (transcript_text, attempts_list)
    Raises: TranscriptError nếu không có captions
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    attempts = []
    session_with_cookies = create_session_with_cookies()
    ytt = YouTubeTranscriptApi(http_client=session_with_cookies)

    # ── Step 1: Discover all available transcripts ──
    discover_attempt = {
        "provider": "youtube-captions:list",
        "status": "pending",
        "error_code": None,
        "error_msg": None,
    }
    try:
        transcript_list = list(ytt.list(video_id))
        discover_attempt["status"] = "success"
        discover_attempt["found"] = [
            f"{t.language_code}({'generated' if getattr(t, 'is_generated', False) else 'manual'})"
            for t in transcript_list
        ]
        attempts.append(discover_attempt)
        print(
            f"📋 Found {len(transcript_list)} transcript(s): "
            + ", ".join(discover_attempt["found"]),
            file=sys.stderr,
        )
    except Exception as e:
        discover_attempt["status"] = "failed"
        discover_attempt["error_code"] = "no_captions"
        discover_attempt["error_msg"] = str(e)[:150]
        attempts.append(discover_attempt)
        raise TranscriptError(
            "YouTube captions không khả dụng cho video này",
            error_code="no_captions",
            provider="youtube-captions",
            attempts=attempts,
        )

    if not transcript_list:
        attempts.append({
            "provider": "youtube-captions:any",
            "status": "failed",
            "error_code": "no_captions",
            "error_msg": "Video has zero transcripts available",
        })
        raise TranscriptError(
            "Video không có captions nào",
            error_code="no_captions",
            provider="youtube-captions",
            attempts=attempts,
        )

    # ── Step 2: Rank and fetch in priority order ──
    ranked = sorted(transcript_list, key=lambda t: rank_transcript(t, lang), reverse=True)

    for transcript_info in ranked:
        lc = transcript_info.language_code
        is_gen = getattr(transcript_info, "is_generated", False)
        score = rank_transcript(transcript_info, lang)
        label = f"{lc}({'generated' if is_gen else 'manual'}, score={score})"

        attempt = {
            "provider": f"youtube-captions:{lc}",
            "status": "pending",
            "error_code": None,
            "error_msg": None,
            "is_generated": is_gen,
            "score": score,
        }
        try:
            t = ytt.fetch(video_id, languages=[lc])
            text = " ".join([snippet.text for snippet in t.snippets])
            if not text.strip():
                attempt["status"] = "failed"
                attempt["error_code"] = "empty_transcript"
                attempt["error_msg"] = f"{label}: empty text"
                attempts.append(attempt)
                continue

            quality = validate_transcript_quality(text)
            if quality["passed"]:
                attempt["status"] = "success"
                attempts.append(attempt)
                print(f"✅ Caption OK: {label}", file=sys.stderr)
                return text.strip(), attempts
            else:
                attempt["status"] = "failed"
                attempt["error_code"] = "empty_transcript"
                attempt["error_msg"] = f"{label}: quality check failed: {quality['reason']}"
                attempts.append(attempt)
                continue

        except Exception as e:
            attempt["status"] = "failed"
            attempt["error_code"] = "no_captions"
            attempt["error_msg"] = f"{label}: {str(e)[:100]}"
            attempts.append(attempt)
            continue

    raise TranscriptError(
        "YouTube captions không khả dụng cho video này",
        error_code="no_captions",
        provider="youtube-captions",
        attempts=attempts,
    )



# =============================================================================
# Layer 2: yt-dlp download → Deepgram STT (FALLBACK)
# =============================================================================

def get_cookies_path() -> str | None:
    """Tìm cookies file: persistent → tmp → None."""
    if COOKIES_PERSISTENT.exists():
        return str(COOKIES_PERSISTENT)
    if COOKIES_TMP.exists():
        return str(COOKIES_TMP)
    return None


def create_session_with_cookies() -> requests.Session:
    """Create a requests.Session with YouTube cookies loaded from cookies file.
    Used by youtube-transcript-api v1.2.4+ via http_client parameter.
    """
    session = requests.Session()
    cookies_path = get_cookies_path()
    if cookies_path:
        try:
            import http.cookiejar
            cj = http.cookiejar.MozillaCookieJar(cookies_path)
            cj.load(ignore_discard=True, ignore_expires=True)
            session.cookies = cj
            print(f"🍪 Loaded {len(list(cj))} cookies from {cookies_path}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ Failed to load cookies: {e}", file=sys.stderr)
    return session



def download_youtube_audio(youtube_url: str, output_dir: str) -> str:
    """
    Download audio từ YouTube bằng yt-dlp → mp3.
    Output vào tempdir, tự cleanup sau.
    Returns path to downloaded mp3 file.
    """
    video_id = extract_video_id(youtube_url)
    if not video_id:
        raise TranscriptError(
            "Invalid YouTube URL",
            error_code="invalid_url",
            provider="yt-dlp"
        )

    output_template = os.path.join(output_dir, f"{video_id}.%(ext)s")

    cookies_path = get_cookies_path()

    # po_token: detect plugin once, warn if missing
    use_pot = detect_pot_provider()
    if not use_pot:
        print(
            "⚠️  yt-dlp-get-pot plugin not found. Install for better YouTube reliability:\n"
            "    pip install yt-dlp-get-pot bgutil-ytdlp-pot-provider\n"
            "    Continuing without po_token (may fail on some videos).",
            file=sys.stderr,
        )
    else:
        print("🔑 po_token provider detected — enabling for yt-dlp.", file=sys.stderr)

    def build_cmd(player_client: str) -> list:
        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "mp3", "--audio-quality", "5",
            "--js-runtimes", "node",
            "--extractor-args", f"youtube:player_client={player_client}",
            "-o", output_template,
            "--no-playlist",
            "--quiet",
            "--no-warnings",
        ]
        if cookies_path:
            cmd += ["--cookies", cookies_path]
        if use_pot:
            # yt-dlp-get-pot integrates automatically as a plugin — no extra args needed
            # The plugin hooks into yt-dlp's extractor via entry points on install
            pass
        cmd.append(youtube_url)
        return cmd

    # Try multiple player_client strategies for bot-detection bypass
    # NOTE: "web" removed — blocked by YouTube 2025 anti-bot; ios/android_vr preferred
    player_clients = ["ios", "android_vr", "mweb", "android"]
    last_error_msg = "yt-dlp failed"
    result = None

    for player_client in player_clients:
        try:
            result = subprocess.run(
                build_cmd(player_client),
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                break
            last_error_msg = result.stderr[:300] if result.stderr else "yt-dlp failed"
            # If bot-detection error, try next client
            if "Sign in" in last_error_msg or "bot" in last_error_msg.lower() or "PO Token" in last_error_msg:
                continue
            # Other errors: no point retrying different player_client
            break
        except subprocess.TimeoutExpired:
            raise TranscriptError(
                "yt-dlp download timeout (180s)",
                error_code="network_timeout",
                provider="yt-dlp"
            )
        except FileNotFoundError:
            raise TranscriptError(
                "yt-dlp not installed",
                error_code="file_not_found",
                provider="yt-dlp"
            )

    if result is None or result.returncode != 0:
        raise TranscriptError(
            f"yt-dlp download failed: {last_error_msg}",
            error_code="download_failed",
            provider="yt-dlp"
        )

    # Find the actual downloaded file
    for ext in ["mp3", "m4a", "webm", "mp4", "opus"]:
        candidate = os.path.join(output_dir, f"{video_id}.{ext}")
        if os.path.exists(candidate):
            return candidate

    raise TranscriptError(
        "Downloaded audio file not found after yt-dlp",
        error_code="file_not_found",
        provider="yt-dlp"
    )


def transcribe_deepgram(
    input_path: str,
    lang: str = "vi",
    session: requests.Session = None,
) -> tuple[str, float]:
    """
    Transcribe file audio/video qua Deepgram nova-2.
    Returns: (transcript, duration_seconds)
    """
    if session is None:
        session = create_session_with_retry()

    audio_file = Path(input_path)
    if not audio_file.exists():
        raise TranscriptError(
            f"File không tồn tại: {input_path}",
            error_code="file_not_found",
            provider="deepgram"
        )

    ext = audio_file.suffix.lower().replace('.', '')
    mime_types = {
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'm4a': 'audio/m4a',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        'mov': 'video/quicktime',
        'mkv': 'video/x-matroska',
        'avi': 'video/x-msvideo'
    }
    mime_type = mime_types.get(ext, 'audio/mpeg')

    try:
        with open(audio_file, "rb") as f:
            resp = session.post(
                DEEPGRAM_URL,
                headers={
                    "Authorization": f"Token {DEEPGRAM_KEY}",
                    "Content-Type": mime_type,
                },
                params={
                    "language": lang,
                    "model": "nova-2",
                    "punctuate": "true",
                    "paragraphs": "true",
                },
                data=f,
                timeout=DEEPGRAM_TIMEOUT,
            )
    except requests.exceptions.Timeout:
        raise TranscriptError(
            "Deepgram request timeout",
            error_code="network_timeout",
            provider="deepgram"
        )
    except requests.exceptions.RequestException as e:
        raise TranscriptError(
            f"Deepgram network error: {str(e)[:100]}",
            error_code="network_timeout",
            provider="deepgram"
        )

    if resp.status_code != 200:
        error_code = classify_http_error(resp.status_code)
        raise TranscriptError(
            f"Deepgram error {resp.status_code}",
            error_code=error_code,
            provider="deepgram"
        )

    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise TranscriptError(
            "Deepgram returned invalid JSON",
            error_code="provider_schema_error",
            provider="deepgram"
        )

    transcript = (
        data.get("results", {})
        .get("channels", [{}])[0]
        .get("alternatives", [{}])[0]
        .get("transcript", "")
    )

    quality = validate_transcript_quality(transcript)
    if not quality["passed"]:
        # Fallback: retry with detect_language=true (video may be in different language)
        print(f"⚠️ Deepgram lang={lang} returned empty/low-quality. Retrying with detect_language=true...", file=sys.stderr)
        try:
            with open(audio_file, "rb") as f2:
                resp2 = (session or create_session_with_retry()).post(
                    DEEPGRAM_URL,
                    headers={
                        "Authorization": f"Token {DEEPGRAM_KEY}",
                        "Content-Type": mime_type,
                    },
                    params={
                        "model": "nova-2",
                        "punctuate": "true",
                        "paragraphs": "true",
                        "detect_language": "true",
                    },
                    data=f2,
                    timeout=DEEPGRAM_TIMEOUT,
                )
            if resp2.status_code == 200:
                data2 = resp2.json()
                transcript2 = (
                    data2.get("results", {})
                    .get("channels", [{}])[0]
                    .get("alternatives", [{}])[0]
                    .get("transcript", "")
                )
                quality2 = validate_transcript_quality(transcript2)
                if quality2["passed"]:
                    detected = data2.get("results", {}).get("channels", [{}])[0].get("detected_language", "unknown")
                    print(f"✅ Deepgram detect_language worked! Detected: {detected}", file=sys.stderr)
                    duration2 = float(data2.get("metadata", {}).get("duration", 0) or 0)
                    return transcript2, duration2
        except Exception as e2:
            print(f"⚠️ Deepgram detect_language retry also failed: {e2}", file=sys.stderr)

        raise TranscriptError(
            f"Deepgram transcript quality check failed: {quality['reason']}",
            error_code="empty_transcript",
            provider="deepgram"
        )

    duration = float(data.get("metadata", {}).get("duration", 0) or 0)
    return transcript, duration


# =============================================================================
# Main pipeline: youtube-transcript-api → yt-dlp + Deepgram
# =============================================================================

def fetch_transcript_with_fallback(
    youtube_url: str,
    lang: str = "vi",
) -> TranscriptResult:
    """
    Fetch transcript with deterministic fallback:
    0. Cache: check file-based cache (7-day TTL) first
    1. Primary: youtube-transcript-api (FREE captions, list()-first)
    2. Fallback: yt-dlp download audio to tempdir → Deepgram STT

    Temp files are ALWAYS cleaned up (success or fail).
    """
    session = create_session_with_retry()
    all_attempts = []
    captions_error = None

    video_id = extract_video_id(youtube_url)
    if not video_id:
        raise TranscriptError(
            "YouTube URL không hợp lệ",
            error_code="invalid_url",
            provider="pipeline"
        )

    # ── Layer 0: Cache check ──
    cached = load_from_cache(video_id, lang)
    if cached:
        print(f"💾 Cache hit: {video_id} (lang={lang})", file=sys.stderr)
        quality = validate_transcript_quality(cached)
        return TranscriptResult(
            transcript=cached,
            provider="cache",
            provider_attempts=[{"provider": "cache", "status": "success", "video_id": video_id}],
            quality_checks=quality,
        )

    # ── Layer 1: youtube-transcript-api ──
    try:
        transcript, attempts = fetch_youtube_captions(video_id, lang)
        all_attempts.extend(attempts)
        quality = validate_transcript_quality(transcript)
        save_to_cache(video_id, lang, transcript)
        return TranscriptResult(
            transcript=transcript,
            provider="youtube-captions",
            provider_attempts=all_attempts,
            quality_checks=quality,
        )
    except TranscriptError as e:
        captions_error = e
        if e.attempts:
            all_attempts.extend(e.attempts)
        all_attempts.append({
            "provider": "youtube-captions",
            "status": "failed",
            "error_code": e.error_code,
            "error_msg": e.message[:100],
        })


    # ── Layer 2: yt-dlp + Deepgram (fallback) ──
    # Download audio to tempdir → transcribe → cleanup
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix="yt_transcript_")

        # Step 2a: Download audio
        download_attempt = {
            "provider": "yt-dlp",
            "status": "pending",
            "error_code": None,
            "error_msg": None,
        }
        try:
            audio_path = download_youtube_audio(youtube_url, temp_dir)
            download_attempt["status"] = "success"
            all_attempts.append(download_attempt)
        except TranscriptError as e:
            download_attempt["status"] = "failed"
            download_attempt["error_code"] = e.error_code
            download_attempt["error_msg"] = e.message[:100]
            all_attempts.append(download_attempt)
            raise TranscriptError(
                f"Tất cả providers đã fail.\n"
                f"  • youtube-captions: {captions_error.message}\n"
                f"  • yt-dlp: {e.message}",
                error_code=e.error_code,
                provider="yt-dlp",
                attempts=all_attempts,
            )

        # Step 2b: Transcribe with Deepgram
        deepgram_attempt = {
            "provider": "deepgram",
            "status": "pending",
            "error_code": None,
            "error_msg": None,
        }
        try:
            transcript, duration = transcribe_deepgram(
                input_path=audio_path,
                lang=lang,
                session=session,
            )
            deepgram_attempt["status"] = "success"
            all_attempts.append(deepgram_attempt)

            quality = validate_transcript_quality(transcript)
            save_to_cache(video_id, lang, transcript)
            return TranscriptResult(
                transcript=transcript,
                provider="deepgram",
                provider_attempts=all_attempts,
                quality_checks=quality,
            )
        except TranscriptError as e:
            deepgram_attempt["status"] = "failed"
            deepgram_attempt["error_code"] = e.error_code
            deepgram_attempt["error_msg"] = e.message[:100]
            all_attempts.append(deepgram_attempt)
            raise TranscriptError(
                f"Tất cả providers đã fail.\n"
                f"  • youtube-captions: {captions_error.message}\n"
                f"  • Deepgram: {e.message}",
                error_code=e.error_code,
                provider="deepgram",
                attempts=all_attempts,
            )

    finally:
        # LUÔN cleanup temp files — không lưu audio trong workspace
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass


# =============================================================================
# Output helpers
# =============================================================================

def save_transcript_with_chunks(
    transcript: str,
    output_path: str,
    chunk_size: int = 0,
    max_chars: int = DEFAULT_MAX_CHARS,
    duration: float = 0.0,
    provider: str = "unknown",
    provider_attempts: list = None,
    quality_checks: dict = None,
    print_stats: bool = False,
):
    """Save transcript + chunks + optional JSON stats."""
    truncated = False
    original_len = len(transcript)

    if max_chars > 0 and original_len > max_chars:
        transcript = transcript[:max_chars]
        truncated = True
        print(f"⚠️ Transcript truncated: {original_len} → {max_chars} chars", file=sys.stderr)

    Path(output_path).write_text(transcript, encoding="utf-8")

    effective_chunk_size = chunk_size if chunk_size > 0 else DEFAULT_CHUNK_SIZE
    chunks = chunk_text(transcript, effective_chunk_size)
    chunk_count = len(chunks)

    if chunk_count > 1:
        for i, chunk in enumerate(chunks, 1):
            chunk_path = f"{output_path}.chunk_{i:03d}.txt"
            Path(chunk_path).write_text(chunk, encoding="utf-8")

    stats = {
        "status": "success",
        "final_provider": provider,
        "provider_attempts": provider_attempts or [],
        "output": output_path,
        "transcript_char_count": len(transcript),
        "original_char_count": original_len,
        "duration_seconds": round(duration, 1),
        "chunk_count": chunk_count,
        "chunk_size": effective_chunk_size,
        "truncated": truncated,
        "quality_checks": quality_checks or {},
    }

    if print_stats:
        print(json.dumps(stats, ensure_ascii=False))
    else:
        print(
            f"✅ Transcript saved: {output_path} "
            f"({len(transcript)} chars, {chunk_count} chunks, provider: {provider}, truncated: {truncated})"
        )


def output_error_stats(
    error_code: str,
    error_msg: str,
    provider_attempts: list,
    print_stats: bool = False,
):
    """Output structured error stats."""
    stats = {
        "status": "fail",
        "error_code": error_code,
        "error_message": error_msg,
        "final_provider": None,
        "provider_attempts": provider_attempts,
        "transcript_char_count": 0,
        "quality_checks": {},
    }

    if print_stats:
        print(json.dumps(stats, ensure_ascii=False))
    else:
        print(f"❌ {error_msg}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", help="Path file audio/video local (Deepgram mode)")
    p.add_argument("--youtube-url", help="YouTube URL (youtube-captions + Deepgram fallback)")
    p.add_argument("--output", default=DEFAULT_OUTPUT)
    p.add_argument("--lang", default="vi")
    p.add_argument("--chunk-size", type=int, default=0,
                   help=f"Chars per chunk. Default auto {DEFAULT_CHUNK_SIZE}")
    p.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                   help=f"Max transcript length. Default {DEFAULT_MAX_CHARS}")
    p.add_argument("--stats", action="store_true", help="Print JSON stats")
    args = p.parse_args()

    if not args.input and not args.youtube_url:
        output_error_stats(
            "invalid_url",
            "Cần --input hoặc --youtube-url",
            [],
            args.stats
        )
        sys.exit(1)

    if args.input and args.youtube_url:
        output_error_stats(
            "invalid_url",
            "Chỉ dùng một trong hai: --input hoặc --youtube-url",
            [],
            args.stats
        )
        sys.exit(1)

    provider_attempts = []

    try:
        if args.youtube_url:
            # Validate URL first
            if not extract_video_id(args.youtube_url):
                output_error_stats(
                    "invalid_url",
                    "YouTube URL không hợp lệ",
                    [],
                    args.stats
                )
                sys.exit(1)

            result = fetch_transcript_with_fallback(args.youtube_url, args.lang)
            save_transcript_with_chunks(
                transcript=result.transcript,
                output_path=args.output,
                chunk_size=args.chunk_size,
                max_chars=args.max_chars,
                duration=0.0,
                provider=result.provider,
                provider_attempts=result.provider_attempts,
                quality_checks=result.quality_checks,
                print_stats=args.stats,
            )
        else:
            # Local file mode with Deepgram
            attempt = {
                "provider": "deepgram",
                "status": "pending",
                "error_code": None,
                "error_msg": None,
            }
            try:
                transcript, duration = transcribe_deepgram(
                    input_path=args.input,
                    lang=args.lang
                )
                quality = validate_transcript_quality(transcript)
                attempt["status"] = "success"
                provider_attempts.append(attempt)

                save_transcript_with_chunks(
                    transcript=transcript,
                    output_path=args.output,
                    chunk_size=args.chunk_size,
                    max_chars=args.max_chars,
                    duration=duration,
                    provider="deepgram",
                    provider_attempts=provider_attempts,
                    quality_checks=quality,
                    print_stats=args.stats,
                )
            except TranscriptError as e:
                attempt["status"] = "failed"
                attempt["error_code"] = e.error_code
                attempt["error_msg"] = e.message[:100]
                provider_attempts.append(attempt)
                raise

    except TranscriptError as e:
        final_attempts = e.attempts if e.attempts else provider_attempts
        output_error_stats(
            e.error_code,
            e.message,
            final_attempts,
            args.stats
        )
        sys.exit(1)
    except Exception as e:
        output_error_stats(
            "unknown",
            str(e)[:200],
            provider_attempts,
            args.stats
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
