#!/usr/bin/env python3
"""Deterministic character-count validator for DND ads assets.

Reads a JSON object from stdin and reports exact, NFC-normalized code-point
counts against each platform's hard limits. Does not judge copy quality.

Input JSON shape (all keys optional):
{
  "titles": ["Bo Kinh Chi 15 Phut", ...],
  "descriptions": ["...", ...],
  "url_paths": ["/mo-mat-can", ...],
  "expected_title_count": 15,
  "expected_description_count": 4
}

Limits (Google RSA hard limits):
  title       <= 30 chars
  description <= 90 chars
  url_path    <= 15 chars

Usage:
  python3 validate_chars.py < input.json
  echo '{"titles": ["..."]}' | python3 validate_chars.py

Exit code: 0 if all checks pass, 1 if any check fails.
"""

import sys
import json
import unicodedata

LIMITS = {
    "titles": 30,
    "descriptions": 90,
    "url_paths": 15,
}


def count_chars(text: str) -> int:
    """Code-point count after NFC normalization (correct for Vietnamese)."""
    return len(unicodedata.normalize("NFC", text))


def validate_field(field_name: str, items, limit: int):
    results = []
    for i, text in enumerate(items, start=1):
        chars = count_chars(text)
        results.append({
            "index": i,
            "text": text,
            "chars": chars,
            "limit": limit,
            "pass": chars <= limit,
        })
    return results


def validate_count(field_name: str, actual: int, expected):
    if expected is None:
        return None
    return {
        "field": field_name,
        "expected": expected,
        "actual": actual,
        "pass": actual == expected,
    }


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"error": "no input received on stdin"}))
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON: {e}"}))
        sys.exit(1)

    output = {}
    all_pass = True
    total_checked = 0
    total_failed = 0

    for field_name, limit in LIMITS.items():
        items = data.get(field_name)
        if items is None:
            continue
        field_results = validate_field(field_name, items, limit)
        output[field_name] = field_results
        total_checked += len(field_results)
        failed = [r for r in field_results if not r["pass"]]
        total_failed += len(failed)
        if failed:
            all_pass = False

    count_checks = []
    title_count_check = validate_count(
        "titles", len(data.get("titles", [])), data.get("expected_title_count")
    )
    if title_count_check:
        count_checks.append(title_count_check)
        if not title_count_check["pass"]:
            all_pass = False

    desc_count_check = validate_count(
        "descriptions",
        len(data.get("descriptions", [])),
        data.get("expected_description_count"),
    )
    if desc_count_check:
        count_checks.append(desc_count_check)
        if not desc_count_check["pass"]:
            all_pass = False

    if count_checks:
        output["count_checks"] = count_checks

    output["summary"] = {
        "total_checked": total_checked,
        "total_failed": total_failed,
        "all_pass": all_pass,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
