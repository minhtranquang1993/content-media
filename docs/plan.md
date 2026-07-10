# Implementation Plan: content-media skill

## Overview
Rename `yt-content` skill to `content-media`, extend input surface (URL + local file), enforce required hashtags per brand via data-driven policy in `brand_profiles.md`, and carve out doctor-voice exception. Reuses existing Deepgram pipeline and cache logic — no rewrite. Deploy through parallel migration (new folder alongside old), then sync canonical repo.

**Local file support — verified**: `yt_transcript.py` lines 984-1072 already implement `--input <path>` mode calling `transcribe_deepgram()` directly. The Deepgram function supports mp3/wav/mp4/webm/m4a/ogg/flac via mime_types dict (lines 645-653). No new code path needed for local files — only SKILL.md workflow updates + mime_types extension. This is verified against existing code, not an assumption.

**Enforcement level — best-effort prompt-level**: Hashtag rules are enforced via SKILL.md instructions read by the agent. This is prompt-level, not deterministic — the agent must remember. No validator script is added in this iteration (over-scope for 2 brands). See Risk Assessment for mitigation.

## Prerequisites Check
Run these before Step 1:
1. `Test-Path C:\Users\Admin\.claude\credentials\yt_content_secrets.json` → expect `True` (already verified).
2. `cd C:\Users\Admin\Desktop\content-media && git status` → expect clean working tree, branch `main`, up to date with `origin/main`.
3. `Test-Path C:\Users\Admin\.claude\skills\yt-content\.cache` → expect `True`.
4. Check Python interpreter version in Git Bash. Confirm 3.12+ (matches `tempfile` behavior on Windows).
5. **Verify local-file mode manually before Step 1**: run `python C:\Users\Admin\.claude\skills\yt-content\scripts\yt_transcript.py --help` → confirm `--input` argument exists in argparse output. Confirms local input pathway is available in current codebase before we plan around it.

If any fails, stop and resolve before touching files.

## Execution Order

Sequencing rule: every step below is safe to stop after. Old skill keeps working until Step 9. New skill becomes usable after Step 4. Repo push (Step 10) happens last.

---

### Step 1 — Copy skill folder yt-content → content-media (parallel deploy)
**Change:** Copy the entire `C:\Users\Admin\.claude\skills\yt-content\` tree to `C:\Users\Admin\.claude\skills\content-media\`, excluding `.cache\*.txt`, `scripts\__pycache__\`, and `scripts\*.bak*` files.
**Files affected:**
- New folder: `C:\Users\Admin\.claude\skills\content-media\` with subfolders `scripts\`, `references\`, `.cache\` (empty).
- Copied: `SKILL.md`, `.gitignore`, `scripts\yt_transcript.py`, `scripts\yt_download.py`, `references\style-dimensions-power-words.md`, `references\brand_profiles.md`, `references\doctor_profiles.md`.
**Line change estimate:** 0 (pure copy).
**Verify:**
- `ls C:\Users\Admin\.claude\skills\content-media\` shows 3 subfolders + SKILL.md + .gitignore.
- Diff each copied file against yt-content source → byte-identical at this stage.
- No `.bak*` or `__pycache__` in destination.
**Rollback:** `rm -rf C:\Users\Admin\.claude\skills\content-media\`. Old skill unaffected.

---

### Step 2 — Update SKILL.md frontmatter + trigger keywords (rename identity)
**Change:** In `C:\Users\Admin\.claude\skills\content-media\SKILL.md`:
- Frontmatter `name: yt-content` → `name: content-media`.
- Frontmatter `description`: broaden to mention "video/audio local hoặc URL YouTube", update trigger phrases: add "content từ video local", "làm content từ file mp4", keep YouTube phrases.
- H1 header "yt-content Skill" → "content-media Skill".
- Trigger section bullet list: add "khi anh gửi đường dẫn file video/audio local (mp4, mov, mp3…)" + keep existing YouTube triggers.
- Doctor Profile Flags example lines: `/yt-content ...` → `/content-media ...`.
- All internal path references `skills/yt-content/scripts/...` → `skills/content-media/scripts/...`.
- Category unchanged (`content-seo`).

**Files affected:** `C:\Users\Admin\.claude\skills\content-media\SKILL.md`
**Line change estimate:** medium (~15-20 lines touched).
**Verify:**
- `grep -c "yt-content" SKILL.md` in content-media folder → expect 0.
- `head -8 SKILL.md` shows `name: content-media`.
- Old file `.claude\skills\yt-content\SKILL.md` still unchanged.
- Invoke `/content-media` with a dummy prompt — trigger should fire.
**Rollback:** Copy `.claude\skills\yt-content\SKILL.md` back over the new one.

---

### Step 3 — Fix `/tmp` hardcoding in scripts (Windows portability)
**Change:** In `C:\Users\Admin\.claude\skills\content-media\scripts\yt_transcript.py`:
- Line 75: `COOKIES_TMP = Path("/tmp/yt_cookies.txt")` → `COOKIES_TMP = Path(tempfile.gettempdir()) / "yt_cookies.txt"`.
- Line 986: argparse `default="/tmp/yt_transcript.txt"` → compute via `str(Path(tempfile.gettempdir()) / "yt_transcript.txt")`. Add module-level constant `DEFAULT_OUTPUT` to keep argparse call readable.
- Docstring lines 11 & 14: replace literal `/tmp/transcript.txt` and `/tmp/yt_audio.mp3` in Usage examples with `<tempdir>/transcript.txt`.
- Comment line ~82 "Audio tạm lưu /tmp" → "Audio tạm lưu tempdir".
- Comment line ~770 "download audio to /tmp" → "download audio to tempdir".

**Note on `tempfile` import in `yt_transcript.py`**: verified `import tempfile` already exists at line 23 of source file (bên cạnh `import time` cùng block). Step 3 chỉ dùng lại, không cần add import mới cho file này.

In `C:\Users\Admin\.claude\skills\content-media\scripts\yt_download.py`:
- Line 48: argparse `default="/tmp/yt_audio.mp3"` → `default=str(Path(tempfile.gettempdir()) / "yt_audio.mp3")`. **Add `import tempfile` ở top** (file này chưa import — verify bằng grep trước khi edit).

**Files affected:** 2 files.
**Line change estimate:** small (~8 lines).
**Verify:**
- `grep -n "/tmp" scripts/yt_transcript.py scripts/yt_download.py` → 0 matches (or only inside docstring examples where explicitly noted as generic).
- `grep -c "^import tempfile" scripts/yt_transcript.py scripts/yt_download.py` → both files phải trả về `1`.
- `python -m py_compile scripts/yt_transcript.py scripts/yt_download.py` → exit 0 (no syntax/import errors).
- Run: `python scripts/yt_transcript.py --help` → argparse `--output` default is a real Windows path like `C:\Users\Admin\AppData\Local\Temp\yt_transcript.txt`.
- Run: `python scripts/yt_download.py --help` → argparse `--output` default là Windows tempdir path.
- Run: `python -c "import tempfile; print(tempfile.gettempdir())"` — confirm resolves on Windows.
**Rollback:** Revert both files from `.claude\skills\yt-content\scripts\` copy.

---

### Step 4 — Extend `mime_types` dict for mov/mkv/avi
**Change:** In `C:\Users\Admin\.claude\skills\content-media\scripts\yt_transcript.py` inside `transcribe_deepgram()` (around lines 645-653), add three entries to the `mime_types` dict:
- `'mov': 'video/quicktime'`
- `'mkv': 'video/x-matroska'`
- `'avi': 'video/x-msvideo'`

**Files affected:** `scripts/yt_transcript.py`
**Line change estimate:** tiny (3 lines).
**Verify:**
- Inspect the dict keys.
- Smoke test (if a small mp4 file is available): `python scripts/yt_transcript.py --input C:\path\to\sample.mp4 --output %TEMP%\test.txt --stats`.
**Rollback:** Remove the three added lines.

---

### Step 5 — Update SKILL.md workflow: input auto-detection + rewrite paths
**Change:** In `.claude\skills\content-media\SKILL.md`:
- Replace the "Workflow" diagram `Input: YouTube/Shorts URL` block with a new `Input: YouTube URL hoặc local file path` block. Add a top-level decision node:
  ```
  Input router:
    ├─ Match YouTube URL regex → Layer 1 (youtube-captions) → fallback Deepgram
    ├─ Path tồn tại trên disk (Windows or POSIX) → Deepgram trực tiếp qua --input
    └─ Không khớp → error "Không nhận diện được input, kiểm tra URL hoặc path"
  ```
- Section "Cách chạy": rewrite Bước 1 and Bước 2:
  - Bước 1 (YouTube URL): existing bash example, path prefix → `skills/content-media/scripts/yt_transcript.py`.
  - Bước 2 (local file): example with `--input "C:\path\to\video.mp4"` (double-quoted, showing space handling).
- Notes section: replace `Cookies file: /root/.openclaw/...` (stale Linux path) with `.claude\credentials\yt_cookies.txt` if present.
- Notes: "KHÔNG lưu audio/video trong workspace — chỉ dùng /tmp" → "chỉ dùng system tempdir (`tempfile.gettempdir()`)".

**Files affected:** `.claude\skills\content-media\SKILL.md`
**Line change estimate:** medium (~25-35 lines).
**Verify:**
- Manual read-through: agent should be able to infer routing from workflow diagram alone.
- Test path detection logic: `"C:\video.mp4"` → local branch. `"https://youtu.be/xxx"` → URL branch. `"asdf"` → error.
**Rollback:** Restore from Step 1 copy.

---

### Step 6 — Add `required_hashtags` data to brand_profiles.md
**Change:** In `.claude\skills\content-media\references\brand_profiles.md`, insert a new section after brand definitions, before "Hashtag pool theo lĩnh vực":

```
## Required Hashtags (per-brand mandatory)

Mandatory tag set MUST xuất hiện trong mọi output (TikTok short_hook, TikTok
full_caption, YouTube description, Threads post) trừ khi rơi vào exception
list (xem SKILL.md workflow → hashtag enforcement).

​```yaml
required_hashtags:
  dnd:
    - "#dnd"
    - "#dndsaigon"
    - "#benhvienmat"
    - "#benhviendnd"
  thanh_hung: []
​```
```

**Files affected:** `references/brand_profiles.md`
**Line change estimate:** small (~15 lines).
**Verify:**
- File still renders as valid markdown.
- Agent can locate + parse the yaml block.
- No changes to existing hashtag pool section.
**Rollback:** Delete the new section.

---

### Step 7 — Wire hashtag enforcement into SKILL.md workflow

**Hashtag policy — 3 explicit exceptions (canonical rule set):**
1. **Doctor voice Facebook post** (profile-bsha/bstuan) → EXEMPT, dùng 2-3 personal BS tag.
2. **TikTok short_hook** (≤150 chars) → EXEMPT from 4-tag rule due to hard char cap. Prioritize `#dnd + #dndsaigon` only if they fit; skip the other 2. This is a stakeholder-approved relaxation for short-form.
3. **Sensitive posts** (cảnh báo bệnh, tin buồn, khủng hoảng) → manual override, 0-2 tag.

All other outputs (TikTok full_caption, YouTube description, Threads post) for brand DND MUST contain all 4 mandatory tags.

**Change:** In `.claude\skills\content-media\SKILL.md`:
- In workflow diagram, add a new step between "Viết Threads post" and profile-flag branch:
  ```
  ├─ 8b. Hashtag enforcement (best-effort, prompt-level):
  │     ├─ Đọc brand từ brand_profiles.md → lấy `required_hashtags[brand]`
  │     ├─ Merge required_hashtags vào output NON-exempt:
  │     │  → TikTok full_caption + YouTube description + Threads post
  │     ├─ Exemptions (3 loại):
  │     │  1. Doctor voice FB post (Step 9)
  │     │  2. TikTok short_hook (≤150 chars, ưu tiên #dnd + #dndsaigon nếu vừa)
  │     │  3. Sensitive posts (cảnh báo bệnh, tin buồn) — 0-2 tag manual
  │     └─ Dedupe hashtag list trước khi trả output
  ```
- In "Bước 3 — Viết content", add a subsection between item 5 (Threads) and item 6 (Facebook BS):
  > **Hashtag mandatory check (brand DND)** — 4 tag `#dnd #dndsaigon #benhvienmat #benhviendnd` PHẢI có ở TikTok full_caption + YouTube description + Threads post. TikTok short_hook (≤150 chars): ưu tiên `#dnd + #dndsaigon` nếu đủ chỗ; nếu không, chọn 1-2 tag phù hợp nhất — không phải ép cả 4 tag. Brand Thành Hưng: `required_hashtags` = `[]`, tuyệt đối không chèn tag DND.
- In "Output Contract (Tier-2)" → add to Definition of Done:
  - Brand DND (non-doctor): 4 hashtag mandatory PHẢI xuất hiện ở YouTube description + Threads + TikTok full_caption.
  - TikTok short_hook (exempt): chứa 1-2 tag ưu tiên `#dnd/#dndsaigon` nếu vừa char cap.
  - Brand Thành Hưng: KHÔNG chứa hashtag DND ở bất kỳ output nào.
  - Doctor voice FB post: KHÔNG chứa 4 tag DND mandatory (xem Step 8).

**Files affected:** `SKILL.md`
**Line change estimate:** medium (~20-30 lines).
**Verify:**
- Manual dry-run: agent produces TikTok caption for DND → hashtags include all 4.
- Dry-run for Thành Hưng brand → hashtags exclude DND tags.
**Rollback:** Revert SKILL.md to Step 5 state.

---

### Step 8 — Doctor-voice hashtag exception (F7)
**Change:** In `.claude\skills\content-media\SKILL.md`:
- In workflow diagram Step 9 (Facebook post doctor voice), append explicit note:
  ```
  │     ├─ Doctor voice EXCEPTION: KHÔNG áp 4 hashtag mandatory DND vào FB post BS
  │     ├─ Chỉ dùng 2-3 hashtag từ personal pool BS (xem doctor_profiles.md)
  │     └─ Không tag bệnh viện trực tiếp
  ```
- In "Bước 3 — Viết content" item 6 (Facebook post BS), reinforce: "Hashtag pool riêng của BS. KHÔNG merge với `required_hashtags[dnd]`."

In `.claude\skills\content-media\references\doctor_profiles.md`:
- Add a short line to "Hướng dẫn chung khi viết Facebook post":
  > 7. **Hashtag rule**: Không áp 4 hashtag mandatory DND (`#dnd #dndsaigon #benhvienmat #benhviendnd`) vào FB post BS. Chỉ dùng 2-3 hashtag từ personal pool BS ở section trên.

**Files affected:** `SKILL.md`, `references/doctor_profiles.md`
**Line change estimate:** small (~8 lines total).
**Verify:**
- Manual dry-run: `/content-media <URL> profile-bsha` → FB post ends with 2-3 BS tags, no `#dnd` etc.
**Rollback:** Remove added lines.

---

### Step 8b — Deprecate old yt-content skill description (trigger deconflict)

**Design constraints (address 3 Round 2 sub-concerns):**
1. **Frontmatter must remain YAML-valid** — schema Claude Code expects: `name:`, `description:` fields. Do NOT add invalid syntax. Description stays a single YAML string, just narrowed in scope.
2. **Explicit invocation must still work** — user gõ `/yt-content <URL>` phải load skill được. Chỉ giảm auto-pick, không phá skill.
3. **No broad keywords in deprecated description** — mục đích là giảm khả năng match generic prompt. Description mới phải NGẮN + narrow + không chứa các phrase generic như "youtube", "content", "caption", "tiktok".

**Change:** In `C:\Users\Admin\.claude\skills\yt-content\SKILL.md`:

Current frontmatter (as-is, do NOT paraphrase from memory — the implement agent must Read the file first):
```
---
name: yt-content
description: >-
  Tạo content từ video YouTube/Shorts: lấy transcript (youtube-captions / Deepgram) → viết caption TikTok + title/description SEO YouTube + hashtag.
  Hỗ trợ doctor profile flags (profile-bsha, profile-bstuan) để tạo thêm Facebook post cá nhân hóa theo giọng bác sĩ.
  Trigger: "tạo content từ link youtube", "viết caption tiktok từ video", "transcript youtube", "làm content từ video", hoặc khi anh gửi link YouTube/Shorts kèm yêu cầu tạo content.
---
```

New frontmatter (replace the description block wholesale — narrow, keyword-free, valid YAML):
```
---
name: yt-content
description: "[DEPRECATED] Legacy alias. Chỉ dùng khi gọi explicit /yt-content."
---
```

Note: description is intentionally keyword-free — no mention of `content`, `youtube`, `tiktok`, `caption`, or any generic phrase. Reason: prevent lexical auto-matcher from ranking this skill on generic prompts. Only explicit `/yt-content` invocation should hit it.

Then add — immediately after the closing `---` of frontmatter, before the existing H1 — a keyword-lean deprecation banner:
```
> ⚠️ **DEPRECATED (2026-07-10)** — Skill này giữ lại tạm thời để backward-compat. Dùng /content-media cho luồng mới.
```

Note: banner intentionally keyword-lean — no `YouTube`, `file local`, `hashtag mandatory`, `doctor exception` phrases. Reason: if Claude Code matcher indexes body/banner in addition to frontmatter, these keywords would re-introduce match risk.

**Do NOT touch** scripts, references, or the rest of SKILL.md body (Trigger section, Workflow, Cách chạy...) — anyone who gọi explicit `/yt-content` sẽ thấy skill vẫn hoạt động y hệt cũ.

**Fallback rule (only if smoke test #11 fails)**: Nếu sau khi sửa frontmatter + banner, Claude Code vẫn auto-pick `/yt-content` cho generic prompt (test #11 fail), thực hiện follow-up minimal edit ở old skill. Phạm vi cho phép **mở rộng** vì matcher có thể đọc body chứ không chỉ frontmatter:

1. **Rút gọn Trigger section** (ưu tiên):
   - Xóa các bullet list generic (VD: "Cần tạo content từ video YouTube/Shorts", "Download audio, transcript, viết caption TikTok, title/description SEO YouTube", "User says: 'tạo content từ link youtube', 'viết caption tiktok từ video'...")
   - Thay bằng dòng duy nhất: `- User gọi explicit /yt-content <URL> (legacy alias — dùng /content-media thay thế)`
2. **Rút gọn deprecation banner** (nếu bước 1 chưa đủ):
   - Được phép cắt banner về câu neutral hơn: `> ⚠️ **DEPRECATED (2026-07-10)** — Legacy alias. Dùng /content-media.`
3. **KHÔNG đụng**: Workflow diagram, Cách chạy, Output Contract, scripts/, references/ — đó là behavior spec khi skill được gọi đích danh.

Chỉ thực hiện fallback nếu test #11 fail. Không làm preemptively vì mỗi lần sửa old skill là thêm rủi ro rollback phức tạp hơn. Nếu fallback vẫn không đủ → escalate cho user, không cố tự fix thêm.

**Files affected:** `C:\Users\Admin\.claude\skills\yt-content\SKILL.md` (frontmatter block + 1-line banner). Nothing else in old skill.
**Line change estimate:** tiny (~5 lines total: 3-line description block + 1 blank line + 1 banner line).

**Verify (3 explicit acceptance criteria):**
1. **Generic auto-routing shifts to `/content-media`**: Trong Claude Code new session, gõ "làm content từ link youtube <URL>" → phải auto-pick `/content-media`, không phải `/yt-content`.
2. **Explicit invocation of old skill still works**: Trong Claude Code, gõ `/yt-content <URL>` trực tiếp → skill cũ vẫn load, chạy pipeline youtube-captions/Deepgram y hệt trước.
3. **Frontmatter/schema still valid**: Sau khi sửa, `head -6 C:\Users\Admin\.claude\skills\yt-content\SKILL.md` phải hiển thị YAML frontmatter đúng dạng (name + description fields, ba dấu `---` đóng mở), Claude Code load skill không lỗi parser.

**Rollback:** Copy original SKILL.md frontmatter block back from `.claude\skills\content-media\SKILL.md`'s pre-edit source (Step 1 kết quả — folder mới có bản y hệt yt-content trước khi Step 2 sửa nó). Nếu Step 2 đã chạy, rollback từ Desktop repo trước push, hoặc reconstruct từ original text ở trên block trong plan này.

---

### Step 9 — Rename memory file + update MEMORY.md index
**Change:**
- Rename `C:\Users\Admin\.claude\projects\C--Users-Admin\memory\yt-content-skill-repo.md` → `content-media-skill-repo.md`.
- Inside renamed file:
  - Frontmatter `name: yt-content-skill-repo` → `name: content-media-skill-repo`.
  - Frontmatter description: "Git repo location for skill /content-media (kế thừa /yt-content)".
  - Body: update "Skill đang active" path from `.claude\skills\yt-content\` → `.claude\skills\content-media\`.
  - Body: note that `.claude\skills\yt-content\` still exists as transitional (1-2 tuần), do not edit directly.
  - Body: update push/pull instructions to reference `content-media` folder.
  - Body: paragraph about parallel migration + which folder is canonical.

- In `MEMORY.md`, update Skills line:
  - `Skill yt-content gắn với repo GitHub minhtranquang1993/content-media: [yt-content-skill-repo.md]` → `Skill content-media gắn với repo GitHub minhtranquang1993/content-media: [content-media-skill-repo.md]`.
  - Add short note: "Skill cũ /yt-content vẫn hoạt động trong 1-2 tuần transition."

**Files affected:** 2 memory files (rename + index).
**Line change estimate:** small (~15 lines total).
**Verify:**
- `Test-Path` for new filename returns True, old False.
- MEMORY.md link target resolves.
**Rollback:** Rename file back, revert MEMORY.md edit.

---

### Step 10 — Sync canonical repo + push to GitHub

**Line-ending hygiene**: Prior push commit (a550637) showed `LF will be replaced by CRLF` warnings — Windows Git auto-converts. To pin behavior and eliminate noisy diffs later:

**Pre-sync — add `.gitattributes` (one-time)**: create `C:\Users\Admin\Desktop\content-media\.gitattributes` with:
```
* text=auto eol=lf
*.py text eol=lf
*.md text eol=lf
```
This normalizes text files to LF in the repo, matching what Claude Code + Python expect on all platforms. Also add to `.claude\skills\content-media\` so both trees stay identical.

**Explicit file preservation**: `.cache/` folder in the skill is `.gitignore`d entirely (`.cache/*.txt`). There is no `.gitkeep` currently. Do NOT add one — the folder is meant to be transient. If future need arises, add `.gitkeep` intentionally.

**Change:** In `C:\Users\Admin\Desktop\content-media\`:
1. Pre-check: run `git ls-files` to list currently-tracked files. Confirm what will be replaced.
2. Add `.gitattributes` if not present (see above).
3. Wipe tracked non-git files: `rm -rf SKILL.md .gitignore references scripts`. `.gitattributes` and `.git/` kept.
4. Copy from `.claude\skills\content-media\` (source of truth): SKILL.md, .gitignore, references/*, scripts/yt_transcript.py, scripts/yt_download.py. Do NOT copy `.cache/`, `__pycache__/`, `.bak*`.
5. `git status` → review diff → stage → commit → push origin main.

Commit message:
> Rename skill yt-content → content-media; add local input, Windows tempdir fix, mime types, required_hashtags

Sync command sketch:
```bash
cd "/c/Users/Admin/Desktop/content-media"

# 1. Pre-check
git ls-files

# 2. Add .gitattributes (once)
cat > .gitattributes <<'EOF'
* text=auto eol=lf
*.py text eol=lf
*.md text eol=lf
EOF

# 3. Wipe tracked
rm -rf SKILL.md .gitignore references scripts

# 4. Copy from canonical
cp "/c/Users/Admin/.claude/skills/content-media/SKILL.md" .
cp "/c/Users/Admin/.claude/skills/content-media/.gitignore" .
cp -r "/c/Users/Admin/.claude/skills/content-media/references" .
mkdir -p scripts
cp "/c/Users/Admin/.claude/skills/content-media/scripts/yt_transcript.py" scripts/
cp "/c/Users/Admin/.claude/skills/content-media/scripts/yt_download.py" scripts/

# 5. Commit + push
git add -A
git status
git commit -m "Rename skill yt-content → content-media; add local file input, Windows tempdir fix, mime types, required_hashtags policy; pin LF line endings"
git push origin main
```

**Also sync `.gitattributes` back to skill folder**: `cp .gitattributes /c/Users/Admin/.claude/skills/content-media/` — keeps both trees identical.

**Files affected:** Desktop repo + 1 new commit + `.gitattributes` in both `.claude` and Desktop.
**Line change estimate:** N/A (mirror of `.claude\skills\content-media\` + 3-line `.gitattributes`).
**Verify:**
- `git status` clean after push.
- `git log --oneline -3` shows new commit.
- **No CRLF warnings** during `git add -A` (expected: pinned by `.gitattributes`).
- GitHub UI shows SKILL.md with `name: content-media` and LF line endings.
- Confirm `.cache/*.txt`, `__pycache__/`, `*.bak*` NOT in the pushed tree via `git ls-tree -r HEAD --name-only`.
**Rollback:** `git revert HEAD && git push` (safe — Desktop repo not tied to any pipeline).

---

## Test Cases (manual smoke)

Run after Step 8, before repo sync.

1. **YouTube URL happy path** — captions available → all 6 required outputs, mandatory DND hashtags present.
2. **YouTube URL fallback** — no captions → Layer 2 yt-dlp + Deepgram succeeds.
3. **Local mp4 file** — auto-detect local path → Deepgram → all outputs.
4. **Local mp3 with space in path** — quoted correctly, Deepgram succeeds.
5. **Local mov/mkv file (F5)** — mime `video/quicktime` sent; success OR clean error (indicates need for N1 ffmpeg fallback).
6. **Doctor profile flag (F7)** — `profile-bsha` → FB post has 2-3 BS tags, NO DND mandatory tags.
7. **Brand Thành Hưng (F6)** — outputs contain vận chuyển hashtags; ZERO DND hashtags.
8. **Backward compat `/yt-content`** — old skill still fires.
9. **Invalid input** — clean error, no crash.
10. **Windows tempdir sanity** — `--help` shows Windows path in default.
11. **Trigger deconflict (Step 8b — generic phrase)** — gõ generic prompt "tạo content từ link youtube <URL>" → Claude Code phải auto-pick `/content-media`, KHÔNG pick `/yt-content` (đã deprecated).
12. **Explicit old-skill invocation (Step 8b — backward-compat)** — gõ đích danh `/yt-content <URL>` → skill cũ vẫn load, vẫn chạy pipeline cũ. Không được "orphan" skill cũ.
13. **Local file route to content-media** — gõ "làm content từ file này: C:\Users\Admin\Videos\test.mp4" → phải auto-pick `/content-media`, gọi `--input` path.

## Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| Skill trigger conflict — Claude Code auto-picks wrong skill | High | **Step 8b** narrows yt-content frontmatter description to keyword-free legacy alias + adds keyword-lean deprecation banner. Trigger section body only trimmed if smoke test #11 fails (conditional fallback). Content-media becomes canonical for generic phrases; old skill still callable by explicit name. |
| Frontmatter rename breaks trigger | High | Verify with dry `/content-media` call immediately after Step 2. Old skill still works. |
| **Hashtag enforcement is prompt-level only, not deterministic** | **Medium (accepted)** | **DoD downgrades wording to "best-effort" — no validator script in this scope.** Reinforced in Output Contract (Tier-2). Manual smoke tests 1, 6, 7 catch regressions. Full validator = future scope. |
| `tempfile.gettempdir()` returns unexpected path on Windows | Low | Verified via Prerequisites check. |
| Desktop repo push overwrites WIP | Medium | Step 10 verifies `git status` clean before starting; reviews diff before commit. |
| Old cached `.cache\*.txt` files invalidate after rename | Low | New folder starts empty cache. Not a bug. |
| Deepgram mime for mkv/avi rejected by API | Low-medium | Test case 5 documents. N1 (ffmpeg fallback) not in this scope — clean error message enough. |
| Deploy Step 1 copies `.bak*`/`__pycache__` | Low | Explicit exclude pattern in copy. Verify step lists directory. |
| Secrets path breaks after rename | Low | Verified: `parents[3]` from `.claude\skills\<any>\scripts\` = `.claude\`. No change. |
| MEMORY.md link stale | Low | Rename + link update in same Step 9. |
| **CRLF line-ending churn on Windows** | **Medium (accepted)** | **Step 10 pins with `.gitattributes` (`* text=auto eol=lf`). No CRLF warnings expected on future pushes.** |
| Local file support assumed but not verified | High (mitigated) | **Prerequisites Check #5 verifies `--input` argument exists via `--help` before Step 1**. Overview explicitly documents the code lines (984-1072) that already implement this. |

## Definition of Done

**Enforcement level note**: Hashtag rules are BEST-EFFORT (prompt-level via SKILL.md, not a validator). Manual smoke testing is the QA layer. All items marked with `[best-effort]` depend on agent follow-through.

- [ ] `/content-media https://youtube.com/...` runs end-to-end, produces all 6 required outputs. (F1, F3)
- [ ] `/content-media C:\path\to\video.mp4` produces transcript via Deepgram + all 6 outputs. (F3)
- [ ] `[best-effort]` DND-brand TikTok full_caption + YouTube description + Threads: all 4 required hashtags present. (F6)
- [ ] `[best-effort]` DND-brand TikTok short_hook: contains `#dnd` + `#dndsaigon` if char cap allows; other 2 tags exempt. (F6, exception 2)
- [ ] `[best-effort]` Doctor voice FB post (`profile-bsha`/`profile-bstuan`): NO 4 mandatory DND hashtags; uses 2-3 personal BS tags. (F7, exception 1)
- [ ] `[best-effort]` Thành Hưng brand outputs: NO DND hashtags anywhere. (F6)
- [ ] `/yt-content` old skill still callable by explicit name during transition (backward-compat). (F2)
- [ ] `/yt-content` frontmatter marked deprecated (keyword-free description + keyword-lean banner). (Step 8b — always)
- [ ] `/yt-content` generic trigger phrases in body removed **only if smoke test #11 fails** (conditional fallback). If test #11 passes at Step 8b baseline, this item is N/A. (Step 8b fallback)
- [ ] GitHub repo `content-media` main branch has new commit with all changes. (F8)
- [ ] `.gitattributes` present in both `.claude\skills\content-media\` and `Desktop\content-media\` with LF eol pinning. (Step 10)
- [ ] No CRLF warnings during Step 10 `git add`. (Step 10)
- [ ] Memory file renamed to `content-media-skill-repo.md`; MEMORY.md index updated. (F8)
- [ ] No `/tmp` literal remaining in Python scripts (grep 0). (F4)
- [ ] `mime_types` dict in `yt_transcript.py` includes `mov/mkv/avi`. (F5)
- [ ] All 13 smoke test cases pass (case 5 exception acceptable if Deepgram rejects raw mkv/avi container — that's future ffmpeg N1 scope).

## Sizing estimate
- 10 steps.
- ~90-130 lines of net edits across 6 files.
- Deploy-safe: every step keeps `/yt-content` operational; new skill fully usable after Step 8; canonical repo aligned after Step 10.
