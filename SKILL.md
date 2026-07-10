---
name: yt-content
description: >-
  Tạo content từ video YouTube/Shorts: lấy transcript (youtube-captions / Deepgram) → viết caption TikTok + title/description SEO YouTube + hashtag.
  Hỗ trợ doctor profile flags (profile-bsha, profile-bstuan) để tạo thêm Facebook post cá nhân hóa theo giọng bác sĩ.
  Trigger: "tạo content từ link youtube", "viết caption tiktok từ video", "transcript youtube", "làm content từ video", hoặc khi anh gửi link YouTube/Shorts kèm yêu cầu tạo content.
---

# yt-content Skill

## Trigger

Use this skill when:
- Cần tạo content từ video YouTube/Shorts
- Download audio, transcript, viết caption TikTok, title/description SEO YouTube
- User says: "tạo content từ link youtube", "viết caption tiktok từ video", "transcript youtube", "làm content từ video"

### Doctor Profile Flags (optional)
Thêm vào cuối lệnh để sinh Facebook post cá nhân hóa theo bác sĩ:
- `profile-bsha` → ThS.BS Lê Thị Thu Hà (Trưởng khoa Khúc xạ)
- `profile-bstuan` → BS Bùi Quang Tuấn (Giám đốc BV)

Ví dụ: `/yt-content https://youtube.com/... profile-bsha`
Ví dụ: `/yt-content https://youtube.com/... profile-bstuan`

## Workflow

```
Input: YouTube/Shorts URL
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
  │     └─ Audio lưu tạm tại /tmp, tự cleanup sau khi xong
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
  ├─ 9. [Nếu có profile flag] Viết Facebook post theo voice bác sĩ
  │     ├─ profile-bsha → giọng ThS.BS Lê Thị Thu Hà (ấm áp, gần gũi)
  │     └─ profile-bstuan → giọng BS Bùi Quang Tuấn (chuyên môn sâu, quyết đoán)
  │     └─ Xem persona & guidelines: references/doctor_profiles.md
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
python3 skills/yt-content/scripts/yt_transcript.py \
  --youtube-url "<youtube_url>" \
  --output /tmp/yt_transcript.txt \
  --stats
```
- Layer 1: youtube-transcript-api — lấy captions FREE, không cần API key
- Layer 2: fallback yt-dlp download → Deepgram nova-2 STT
- Audio tạm lưu /tmp, tự cleanup

### Bước 2 — Transcript từ file local (Deepgram trực tiếp)
```bash
python3 skills/yt-content/scripts/yt_transcript.py \
  --input /tmp/yt_audio.mp3 \
  --output /tmp/yt_transcript.txt \
  --stats
```

- `--stats` trả JSON: `final_provider`, `char_count`, `chunk_count`, `duration_seconds`, `truncated`
- Nếu `chunk_count > 1`: đọc từng chunk file, tóm tắt, rồi viết content từ summary

### Bước 3 — Viết content
Đọc transcript từ `/tmp/yt_transcript.txt`, xác định brand (xem `references/brand_profiles.md`), rồi viết:
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

## Notes
- Cookies file: `/root/.openclaw/workspace/credentials/yt_cookies.txt` (cho yt-dlp fallback)
- Deepgram key trong `credentials/yt_content_secrets.json`
- Brand profiles + hashtag pool: `references/brand_profiles.md`
- Output mặc định: private draft → anh duyệt → public
- **KHÔNG lưu audio/video trong workspace** — chỉ dùng /tmp, tự cleanup

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

## Category
content-seo
