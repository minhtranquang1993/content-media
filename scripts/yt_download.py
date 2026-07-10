#!/usr/bin/env python3
"""
yt_download.py — Download audio từ YouTube/Shorts về mp3
Usage:
  python3 scripts/yt_download.py --url "https://youtube.com/shorts/xxx" --output /tmp/yt_audio.mp3
  python3 scripts/yt_download.py --url "https://youtu.be/xxx" --cookies /tmp/yt_cookies.txt --output /tmp/yt_audio.mp3
"""

import argparse
import subprocess
import sys
from pathlib import Path

import os as _os_cred
_WORKSPACE_ROOT = _os_cred.path.dirname(_os_cred.path.dirname(_os_cred.path.dirname(_os_cred.path.dirname(_os_cred.path.abspath(__file__)))))
COOKIES_DEFAULT = _os_cred.path.join(_WORKSPACE_ROOT, "credentials", "yt_cookies.txt")  # CRED_MIGRATED: 2026-04-11


def download(url: str, output: str, cookies: str = None) -> bool:
    cookies_file = cookies or COOKIES_DEFAULT
    out_template = output.replace(".mp3", ".%(ext)s")

    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "--js-runtimes", "node",
        "--remote-components", "ejs:github",
        "-o", out_template,
    ]

    if Path(cookies_file).exists():
        cmd += ["--cookies", cookies_file]

    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ yt-dlp error:\n{result.stderr[:500]}", file=sys.stderr)
        return False

    print(f"✅ Audio saved: {output}")
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--output", default="/tmp/yt_audio.mp3")
    p.add_argument("--cookies", default=None)
    args = p.parse_args()

    ok = download(args.url, args.output, args.cookies)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
