# Handover — content-media skill migration

**Session date:** 2026-07-10
**Status:** Plan APPROVED by Codex (6 rounds). Implementation NOT STARTED.

---

## What was done in this session

1. **Brainstorm** — feature list + Codex peer debate (2 rounds, effort=high) → consensus on all technical decisions.
2. **Brief** written: `docs/content-media-brief.md`
3. **Plan** written: `docs/plan.md` (10 steps + Step 8b)
4. **Codex Plan Review** — 6 rounds debate → **APPROVE** on Round 6. Plan is implementation-ready.
5. **Deepgram credentials** saved at `C:\Users\Admin\.claude\credentials\yt_content_secrets.json` (already on disk, not in repo).

## What's NOT done yet

- Implementation of 10 Steps + Step 8b
- Codex Implementation Review (Cook Phase 4)
- Final Report (Cook Phase 5)

---

## Where to pick up tonight

Open Claude Code in `C:\Users\Admin\` và nói:

> "Tiếp tục cook implementation phase từ session sáng — đọc `Desktop\content-media\docs\plan.md` và thực hiện 10 steps."

Hoặc dán prompt sau vào Claude Code (đã test-ready cho implementation agent):

```
Bạn là implementation agent cho Cook Phase 3. Đọc plan đã được Codex APPROVE
ở C:\Users\Admin\Desktop\content-media\docs\plan.md và thực hiện đúng 10 Steps
+ Step 8b theo thứ tự. Match style code hiện có. Verify sau mỗi Step. Không
chạy Step 10 (git push) nếu Steps 1-9 chưa xong. Report cuối theo template
trong plan.md.
```

---

## Todo list (order matters)

### Prerequisites Check (chạy trước Step 1)
- [ ] `Test-Path C:\Users\Admin\.claude\credentials\yt_content_secrets.json` → True
- [ ] `cd C:\Users\Admin\Desktop\content-media && git status` → clean, on main, up-to-date
- [ ] `Test-Path C:\Users\Admin\.claude\skills\yt-content\.cache` → True
- [ ] Python 3.12+ available in Git Bash
- [ ] `python C:\Users\Admin\.claude\skills\yt-content\scripts\yt_transcript.py --help` → argparse shows `--input` argument

### Step 1 — Copy yt-content folder → content-media (parallel deploy)
- [ ] Copy `.claude\skills\yt-content\` → `.claude\skills\content-media\`, exclude `.cache\*.txt`, `scripts\__pycache__\`, `scripts\*.bak*`
- [ ] Verify: 3 subfolders + SKILL.md + .gitignore in new folder; no bak/pycache

### Step 2 — Update SKILL.md frontmatter (rename identity)
- [ ] Frontmatter `name: yt-content` → `name: content-media`
- [ ] Description broaden: mention "video/audio local hoặc URL YouTube"
- [ ] H1 header + Doctor Profile examples + internal path refs
- [ ] Verify: `grep -c "yt-content" SKILL.md` = 0

### Step 3 — Fix `/tmp` hardcoding (Windows portability)
- [ ] `yt_transcript.py`: `COOKIES_TMP`, argparse default `--output`, docstring/comments — all `/tmp` → `tempfile.gettempdir()`. Note: `import tempfile` đã có ở line 23, KHÔNG add lại.
- [ ] `yt_download.py`: argparse default `--output` + **add `import tempfile`** ở top (file này chưa import).
- [ ] Verify:
  - `grep -n "/tmp" scripts/*.py` = 0 matches
  - `grep -c "^import tempfile" scripts/yt_transcript.py scripts/yt_download.py` = both 1
  - `python -m py_compile scripts/*.py` exit 0
  - `python scripts/yt_transcript.py --help` → default là Windows path

### Step 4 — Extend `mime_types` for mov/mkv/avi
- [ ] Add 3 entries trong `transcribe_deepgram()` dict:
  - `'mov': 'video/quicktime'`
  - `'mkv': 'video/x-matroska'`
  - `'avi': 'video/x-msvideo'`

### Step 5 — SKILL.md workflow: input auto-detection
- [ ] Replace workflow diagram: add Input router (URL vs local path vs error)
- [ ] Rewrite "Cách chạy": Bước 1 (URL), Bước 2 (local file với path quoted C:\...)
- [ ] Notes: bỏ Linux `/root/.openclaw/...` path, thay bằng `.claude\credentials\yt_cookies.txt`
- [ ] Notes: "chỉ dùng /tmp" → "chỉ dùng system tempdir"

### Step 6 — Add `required_hashtags` data to brand_profiles.md
- [ ] Thêm section "Required Hashtags (per-brand mandatory)" với YAML block:
  ```yaml
  required_hashtags:
    dnd:
      - "#dnd"
      - "#dndsaigon"
      - "#benhvienmat"
      - "#benhviendnd"
    thanh_hung: []
  ```

### Step 7 — Wire hashtag enforcement into SKILL.md (best-effort)
- [ ] Workflow diagram: thêm step "8b. Hashtag enforcement" với 3 exceptions
- [ ] "Bước 3" thêm subsection "Hashtag mandatory check (brand DND)"
- [ ] Output Contract: thêm 4 items vào Definition of Done (DND, TikTok short_hook exempt, Thành Hưng, Doctor voice)

### Step 8 — Doctor-voice hashtag exception (F7)
- [ ] SKILL.md Step 9 (FB post BS): thêm block "Doctor voice EXCEPTION"
- [ ] Reinforce ở "Bước 3" item 6
- [ ] `references/doctor_profiles.md`: thêm rule 7 "Hashtag rule"

### Step 8b — Deprecate old yt-content skill
- [ ] `.claude\skills\yt-content\SKILL.md`: frontmatter description → keyword-free `"[DEPRECATED] Legacy alias. Chỉ dùng khi gọi explicit /yt-content."`
- [ ] Thêm banner keyword-lean sau frontmatter: `⚠️ DEPRECATED (2026-07-10) — Skill này giữ lại tạm thời để backward-compat. Dùng /content-media cho luồng mới.`
- [ ] KHÔNG đụng scripts, references, workflow body
- [ ] Verify 3 tiêu chí: generic prompt routes to content-media / explicit /yt-content still works / frontmatter YAML valid

### Step 9 — Rename memory file + update MEMORY.md
- [ ] Rename `yt-content-skill-repo.md` → `content-media-skill-repo.md`
- [ ] Update frontmatter + body content (path references)
- [ ] Update MEMORY.md skills line

### Step 10 — Sync canonical repo + push
- [ ] Add `.gitattributes` với `* text=auto eol=lf`, `*.py text eol=lf`, `*.md text eol=lf` ở cả 2 nơi (skill folder + Desktop repo)
- [ ] Wipe tracked files trong Desktop repo (giữ .git + .gitattributes)
- [ ] Copy fresh từ `.claude\skills\content-media\`
- [ ] `git add -A` → verify no CRLF warnings → commit → push origin main
- [ ] Commit message: `Rename skill yt-content → content-media; add local file input, Windows tempdir fix, mime types, required_hashtags policy; pin LF line endings`

### Quality Gate (sau Step 10)
- [ ] L1 Build: `py_compile` exit 0
- [ ] L2 Regression: N/A (no test suite)
- [ ] L3 Standards: grep checks pass
- [ ] L4 Plan Coverage: mỗi Step map tới edit cụ thể

### Manual smoke tests (13 cases — cần Claude Code UI live)
- [ ] #1 YouTube URL happy path (captions available)
- [ ] #2 YouTube fallback (no captions → yt-dlp + Deepgram)
- [ ] #3 Local mp4 file
- [ ] #4 Local mp3 với space in path
- [ ] #5 Local mov/mkv (có thể fail nếu Deepgram reject — case này là future ffmpeg N1 scope)
- [ ] #6 Doctor `profile-bsha` — FB post KHÔNG có 4 DND tags
- [ ] #7 Brand Thành Hưng — outputs KHÔNG có DND tags
- [ ] #8 Backward-compat: `/yt-content` explicit still works
- [ ] #9 Invalid input → clean error
- [ ] #10 Windows tempdir sanity trong `--help`
- [ ] #11 Generic prompt "làm content từ link youtube" → auto-pick `/content-media`
- [ ] #12 Explicit `/yt-content <URL>` still loads old skill
- [ ] #13 Local file prompt routes to `/content-media`

### Cook Phase 4 — Codex Implementation Review
- [ ] Chạy code-review skill hoặc codex-impl-review với plan.md + working tree diff
- [ ] Address issues (accept/dispute)
- [ ] Iterate until APPROVE hoặc stalemate

### Cook Phase 5 — Final Report
- [ ] Tổng kết files changed, quality gate score, deviations from plan
- [ ] Cleanup: `HANDOVER.md` này có thể xóa sau khi hoàn thành

---

## Key files reference

| File | Purpose |
|---|---|
| `docs/content-media-brief.md` | Feature list + success criteria |
| `docs/plan.md` | 10-step implementation plan (Codex-approved) |
| `docs/HANDOVER.md` (this) | Todo list + session context |
| `C:\Users\Admin\.claude\skills\yt-content\` | Current active skill (source of Step 1 copy) |
| `C:\Users\Admin\.claude\skills\content-media\` | Target folder (created in Step 1) |
| `C:\Users\Admin\Desktop\content-media\` | Canonical git repo (Step 10 push target) |
| `C:\Users\Admin\.claude\credentials\yt_content_secrets.json` | Deepgram key (already set) |

---

## Key decisions locked in (do NOT re-debate)

- **No symlink/junction** trên Windows → 2 folder song song 1-2 tuần
- **Canonical source** = Desktop repo; **deployed** = `.claude\skills\...`
- **Hashtag enforcement** = prompt-level best-effort, KHÔNG viết validator script
- **ffmpeg** = optional reliability enhancer, KHÔNG dependency gate (mkv/avi fallback là future N1)
- **Trigger deconflict** = deprecate yt-content description (keyword-free) + keyword-lean banner
- **Exceptions hashtag** = 3 cases: doctor voice, TikTok short_hook (≤150 chars), sensitive posts

## Files in this handover push

- `docs/HANDOVER.md` (this file)
- `docs/content-media-brief.md`
- `docs/plan.md`
