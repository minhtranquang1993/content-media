---
name: content-media
description: >-
  Tạo content từ video/audio local hoặc URL YouTube/Shorts: lấy transcript (youtube-captions / Deepgram) → viết caption TikTok + title/description SEO YouTube + hashtag.
  Hỗ trợ doctor profile flags (profile-bsha, profile-bstuan) để tạo thêm Facebook post cá nhân hóa theo giọng bác sĩ.
  Trigger: "tạo content từ link youtube", "làm content từ video local", "làm content từ file mp4", "viết caption tiktok từ video", "transcript youtube", "làm content từ video", hoặc khi anh gửi link YouTube/Shorts / đường dẫn file video-audio kèm yêu cầu tạo content.
---

# content-media Skill

## Trigger

Use this skill when:
- Cần tạo content từ video YouTube/Shorts
- Cần tạo content từ file video/audio local (mp4, mov, mp3, wav, m4a...)
- Download audio, transcript, viết caption TikTok, title/description SEO YouTube
- User says: "tạo content từ link youtube", "làm content từ video local", "làm content từ file mp4", "viết caption tiktok từ video", "transcript youtube", "làm content từ video"
- Khi anh gửi đường dẫn file video/audio local (mp4, mov, mp3…)

### Doctor Profile Flags (optional)
Thêm vào cuối lệnh để sinh Facebook post cá nhân hóa theo bác sĩ:
- `profile-bsha` → ThS.BS Lê Thị Thu Hà (Trưởng khoa Khúc xạ)
- `profile-bstuan` → BS Bùi Quang Tuấn (Giám đốc BV)

Ví dụ: `/content-media https://youtube.com/... profile-bsha`
Ví dụ: `/content-media "C:\Users\Admin\Videos\test.mp4" profile-bstuan`

## Workflow

```
Input: YouTube URL hoặc local file path
  │
Input router:
  ├─ Match YouTube URL regex → Layer 1 (youtube-captions) → fallback Deepgram
  ├─ Path tồn tại trên disk (Windows or POSIX) → Deepgram trực tiếp qua --input
  └─ Không khớp → error "Không nhận diện được input, kiểm tra URL hoặc path"
  │
  ├─ 0. Cache check — file-based, 7-day TTL (FREE, tức thì)
  │     └─ Hit → skip Layer 1 & 2 hoàn toàn
  ├─ 1. Transcript trực tiếp — youtube-transcript-api (FREE, nhanh, không cần key)
  │     └─ list()-first: discover TẤT CẢ captions → rank → fetch best match
  │        Priority: manual vi* > generated a.vi/vi-VR > generated vi* > manual en > generated en > any
  ├─ 2. Fallback khi captions không có: Download audio (mp3) — yt-dlp
  │     └─ player_client: [ios, android_vr, mweb, android] (web đã bỏ - bị block)
  │     └─ po_token: auto-detect yt-dlp-get-pot plugin, dùng nếu có
  ├─ 3. Transcript fallback — Deepgram nova-2 (tiếng Việt)
  │     └─ Audio lưu tạm tại system tempdir, tự cleanup sau khi xong
  │
  ├─ 4. Xử lý transcript (CHUNK-SAFE):
  │     ├─ < 12k chars → đọc trực tiếp
  │     └─ ≥ 12k chars → đọc từng chunk, tóm tắt, discard
  │
  ├─ 5. Viết caption TikTok — 2 VARIANTS:
  │     ├─ short_hook: hook mạnh, max 150 ký tự (dùng làm caption khi đăng)
  │     └─ full_caption: hook + body + CTA + hashtag, 400-900 ký tự (max 2200)
  ├─ 6. Viết title YouTube SEO
  ├─ 7. Viết description YouTube SEO
  ├─ 8. Viết Threads post (max 500 ký tự, casual, hook-first)
  ├─ 8b. Hashtag enforcement (best-effort, prompt-level):
  │     ├─ Đọc brand từ brand_profiles.md → lấy `required_hashtags[brand]`
  │     ├─ Merge required_hashtags vào output NON-exempt:
  │     │  → TikTok full_caption + YouTube description + Threads post
  │     ├─ Exemptions (3 loại):
  │     │  1. Doctor voice FB post (Step 9)
  │     │  2. TikTok short_hook (≤150 chars, ưu tiên #dnd + #dndsaigon nếu vừa)
  │     │  3. Sensitive posts (cảnh báo bệnh, tin buồn) — 0-2 tag manual
  │     └─ Dedupe hashtag list trước khi trả output
  ├─ 9. [Nếu có profile flag] Viết Facebook post theo voice bác sĩ
  │     ├─ profile-bsha → giọng ThS.BS Lê Thị Thu Hà (ấm áp, gần gũi)
  │     ├─ profile-bstuan → giọng BS Bùi Quang Tuấn (chuyên môn sâu, quyết đoán)
  │     ├─ Xem persona & guidelines: references/doctor_profiles.md
  │     ├─ Doctor voice EXCEPTION: KHÔNG áp 4 hashtag mandatory DND vào FB post BS
  │     ├─ Chỉ dùng 2-3 hashtag từ personal pool BS (xem doctor_profiles.md)
  │     └─ Không tag bệnh viện trực tiếp
  └─ 10. Trả anh duyệt
```

## ⚠️ Context Safety Rules

1. **KHÔNG BAO GIỜ** đọc toàn bộ raw transcript > 12k chars vào context cùng lúc
2. Transcript dài → đọc chunk → tóm tắt → discard → đọc chunk tiếp
3. Viết content từ **summary**, không từ raw transcript dài
4. Video > 60 phút → cảnh báo anh trước khi làm

## References
- `references/style-dimensions-power-words.md` — Style Dimensions (TikTok caption profile) + Power Words tiếng Việt
- `references/brand_profiles.md` — Brand profiles, hashtag pool, content guidelines
- `references/doctor_profiles.md` — Doctor personas: BS Hà (profile-bsha) & BS Tuấn (profile-bstuan). Dùng khi có doctor profile flag.

## Cách chạy

### Bước 1 — Transcript từ YouTube URL (youtube-captions → Deepgram fallback)
```bash
python3 skills/content-media/scripts/yt_transcript.py \
  --youtube-url "<youtube_url>" \
  --output <tempdir>/yt_transcript.txt \
  --stats
```
- Layer 1: youtube-transcript-api — lấy captions FREE, không cần API key
- Layer 2: fallback yt-dlp download → Deepgram nova-2 STT
- Audio tạm lưu system tempdir, tự cleanup

### Bước 2 — Transcript từ file local (Deepgram trực tiếp)
```bash
python3 skills/content-media/scripts/yt_transcript.py \
  --input "C:\path\to\video.mp4" \
  --output <tempdir>/yt_transcript.txt \
  --stats
```
- Path local luôn quote bằng dấu ngoặc kép để xử lý đúng khoảng trắng trong path

- `--stats` trả JSON: `final_provider`, `char_count`, `chunk_count`, `duration_seconds`, `truncated`
- Nếu `chunk_count > 1`: đọc từng chunk file, tóm tắt, rồi viết content từ summary

### Bước 3 — Viết content
Đọc transcript từ output file (`--output`), xác định brand (xem `references/brand_profiles.md`), rồi viết:
1. **Caption TikTok — short_hook** — hook mạnh, max 150 ký tự, 2-3 hashtag, 1-2 emoji
2. **Caption TikTok — full_caption** — hook + body + CTA, 400-900 ký tự (max 2200), 5 hashtag
3. **Title YouTube** — có keyword chính, max 70 ký tự
4. **Description YouTube** — 300-500 từ, chuẩn SEO, có CTA + thông tin liên hệ + hashtag
5. **Threads post** — max 500 ký tự, casual tone, hook-first, không cần link preview
6. **[Optional] Facebook post (BS)** — nếu có `profile-bsha` hoặc `profile-bstuan`:
   - Đọc persona từ `references/doctor_profiles.md`
   - Viết 200-380 ký tự, ngôi thứ nhất, theo voice bác sĩ tương ứng
   - Chọn 1 điểm nổi bật từ video, diễn giải qua lăng kính chuyên môn của BS
   - 2-3 hashtag cuối (không link, không tag bệnh viện trực tiếp)
   - Hashtag pool riêng của BS. KHÔNG merge với `required_hashtags[dnd]`.

#### Hashtag mandatory check (brand DND)
4 tag `#dnd #dndsaigon #benhvienmat #benhviendnd` PHẢI có ở TikTok full_caption + YouTube description + Threads post. TikTok short_hook (≤150 ký tự): ưu tiên `#dnd + #dndsaigon` nếu đủ chỗ; nếu không, chọn 1-2 tag phù hợp nhất — không phải ép cả 4 tag. Brand Thành Hưng: `required_hashtags` = `[]`, tuyệt đối không chèn tag DND.

## Notes
- Cookies file: `.claude\credentials\yt_cookies.txt` (cho yt-dlp fallback, nếu có)
- Deepgram key trong `credentials/yt_content_secrets.json`
- Brand profiles + hashtag pool: `references/brand_profiles.md`
- Output mặc định: private draft → anh duyệt → public
- **KHÔNG lưu audio/video trong workspace** — chỉ dùng system tempdir (`tempfile.gettempdir()`), tự cleanup

## Output Contract (Tier-2)

**Output bắt buộc (luôn có):**
- Transcript status: success/fallback/cache/fail + nguồn (cache/youtube-captions/deepgram)
- TikTok short_hook (≤150 ký tự)
- TikTok full_caption (400-900 ký tự, max 2200)
- YouTube title
- YouTube description
- Threads post (≤500 ký tự)
- Hashtag set

**Output optional (chỉ có khi có doctor profile flag):**
- `profile-bsha` → **Facebook post — Góc nhìn BS Hà** (200-380 ký tự, ngôi thứ nhất, tone ấm áp)
- `profile-bstuan` → **Facebook post — Góc nhìn BS Tuấn** (200-380 ký tự, ngôi thứ nhất, tone chuyên môn)
- Cả 2 flag cùng lúc → 2 Facebook posts riêng biệt

**Definition of Done:**
- Có đủ 6 output bắt buộc kể cả khi transcript dùng fallback
- Nếu có doctor profile flag: có thêm Facebook post theo đúng persona
- Nếu transcript fail hoàn toàn: phải báo rõ lý do + phương án xử lý
- Brand DND (non-doctor): 4 hashtag mandatory PHẢI xuất hiện ở YouTube description + Threads + TikTok full_caption.
- TikTok short_hook (exempt): chứa 1-2 tag ưu tiên `#dnd/#dndsaigon` nếu vừa char cap.
- Brand Thành Hưng: KHÔNG chứa hashtag DND ở bất kỳ output nào.
- Doctor voice FB post: KHÔNG chứa 4 tag DND mandatory (xem Step 8).

## Category
content-seo
