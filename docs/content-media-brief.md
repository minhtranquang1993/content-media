# Project Brief: content-media skill (evolution from yt-content)

## Vấn đề
Skill `yt-content` hiện chỉ nhận YouTube URL. Anh cần workflow tổng quát hơn: input video/audio local trên máy → tự transcript + viết content. Hashtag bắt buộc 4 tag DND (#dnd #dndsaigon #benhvienmat #benhviendnd) chưa được enforce ở đâu, dễ quên khi tạo caption.

## Giải pháp
Rename `yt-content` → `content-media`, mở rộng input (URL + local path), enforce hashtag mandatory theo brand + có ngoại lệ cho doctor voice / sensitive post. Reuse code Deepgram + cache hiện có, không viết lại từ đầu.

## MVP Features (bắt buộc cho version đầu tiên)
- [ ] **F1 — Rename skill**: tạo folder mới `.claude\skills\content-media\` (copy từ yt-content), đổi frontmatter `name: content-media`, update trigger keywords, doc reference nội bộ. Verify `/content-media` chạy end-to-end.
- [ ] **F2 — Giữ folder cũ `.claude\skills\yt-content\` song song 1-2 tuần**: sync content từ folder mới, không edit trực tiếp folder cũ.
- [ ] **F3 — Local file input trong workflow**:
  - SKILL.md: mô tả cách nhận diện input (URL vs local path)
  - Auto-detect input type: nếu match URL YouTube → flow cũ; nếu match path tồn tại → gọi `yt_transcript.py --input`; nếu không → error rõ ràng
  - Hỗ trợ path có space + Windows path (`C:\...`)
- [ ] **F4 — Fix Windows `/tmp`**: thay `/tmp` hardcoded trong `yt_transcript.py` bằng `tempfile.gettempdir()`
- [ ] **F5 — Mở rộng mime_types**: thêm `.mov` (video/quicktime), `.mkv` (video/x-matroska), `.avi` (video/x-msvideo)
- [ ] **F6 — Hashtag mandatory theo brand**:
  - `references/brand_profiles.md`: thêm field `required_hashtags` cho DND = `[#dnd, #dndsaigon, #benhvienmat, #benhviendnd]`, cho Thành Hưng = `[]`
  - `SKILL.md` workflow: đọc `required_hashtags` theo brand → merge với hashtag ngữ cảnh → dedupe
- [ ] **F7 — Doctor voice exception**: rule "4 hashtag mandatory" KHÔNG apply cho Facebook post `profile-bsha`/`profile-bstuan`. Post BS giữ 2-3 hashtag như hiện tại, không tag BV trực tiếp.
- [ ] **F8 — Sync repo GitHub**: push đổi tên + code mới lên `minhtranquang1993/content-media` (canonical). Cập nhật memory `yt-content-skill-repo.md` sang `content-media-skill-repo.md`.

## Nice-to-have (làm sau nếu còn thời gian)
- **N1 — ffmpeg fallback** cho mkv/avi khi direct Deepgram upload fail. ffmpeg là optional dependency, không phải hard requirement — nếu không có → báo lỗi actionable cho user.
- **N2 — Cache key mở rộng cho local file**: hash key = `abs_path + mtime + size`, reuse cache 7-day TTL hiện có.
- **N3 — Output QA guardrail** (lightweight): trước khi trả result, kiểm tra brand đúng chưa, hashtag required đã có, không lẫn hashtag brand khác.
- **N4 — Warning file lớn**: cảnh báo user nếu file > threshold size hoặc duration > threshold. Không dựa vào API limit số cụ thể của Deepgram.

## Tương lai (không làm trong lần này)
- Multi-platform link (TikTok/Facebook Reels/IG Reels) qua yt-dlp
- Visual/scene understanding (frame extract + vision model)
- Auto-publish thẳng TikTok/YouTube API
- Structured brand config + validator (over-scope với 2 brand)

## Hướng kỹ thuật (từ Codex debate — consensus)

### Rename & deploy
- **Canonical source**: `C:\Users\Admin\Desktop\content-media\` (git repo)
- **Deployed copy**: `C:\Users\Admin\.claude\skills\content-media\` (Claude Code load)
- **Không symlink/junction** trên Windows — rủi ro debug > lợi ích
- **Transition**: `.claude\skills\yt-content\` giữ 1-2 tuần, sync từ folder mới (không edit tay)
- **Sync flow**: sửa ở repo → copy sang `.claude`. Nếu hotfix trực tiếp `.claude` → back-port ngay về repo.

### Local input handling
- Direct Deepgram upload cho container phổ biến (mp3/wav/mp4/webm/m4a/ogg/flac + mở rộng mov/mkv/avi)
- ffmpeg chỉ là reliability enhancer, KHÔNG dependency gate
- Cache key theo `path + mtime + size` (Phase 1), content hash chỉ khi cần (Phase 2)

### Hashtag policy
- Data (brand_profiles.md): định nghĩa `required_hashtags` per-brand
- Logic (SKILL.md workflow): đọc → merge → dedupe
- Ngoại lệ áp dụng cho:
  - Doctor voice Facebook post (2-3 tag, không tag BV)
  - Sensitive posts (cảnh báo bệnh, tin buồn, khủng hoảng — 0-2 tag)
  - Short-form (caption cực ngắn)
- Thứ tự quyết định hashtag: Publisher/channel → Post intent → Voice

### Lưu ý (pitfalls)
- Skill folder `.claude\skills\yt-content\` KHÔNG phải git repo — Claude Code load skill từ đây, git repo ở Desktop
- Đổi tên folder mà chưa update frontmatter → có thể mất trigger
- Deepgram key hiện đã lưu ở `C:\Users\Admin\.claude\credentials\yt_content_secrets.json` (path này cần verify: script tính `WORKSPACE_ROOT = parents[3]` từ scripts/, nếu rename skill folder thì đường dẫn secrets vẫn = `.claude/credentials/` (parents[3] không đổi))

## Scope & Constraints
- **Đối tượng**: user (anh Minh) — dùng để tạo content DND & Thành Hưng
- **Platform**: Windows 11, Git Bash, Python 3.12/3.14
- **Không được nhồi hashtag DND vào brand Thành Hưng** (khác lĩnh vực y tế/vận chuyển)
- **Deepgram**: 1 key duy nhất, không rotation
- **Backward compat**: giữ `/yt-content` trigger tạm thời, không phá workflow đang dùng

## Success Criteria
1. `/content-media <YouTube URL>` chạy end-to-end như `/yt-content` cũ
2. `/content-media C:\path\to\video.mp4` cho ra transcript + content đầy đủ
3. Mọi output DND (TikTok/YouTube/Threads) có đủ 4 hashtag mandatory
4. Output doctor voice (profile-bsha/bstuan) KHÔNG bị nhồi 4 hashtag
5. Output brand Thành Hưng KHÔNG có hashtag DND
6. `/yt-content` cũ vẫn chạy được trong transition period
7. Repo GitHub `content-media` chứa code mới, memory `yt-content-skill-repo.md` được cập nhật

## Next: /cook
