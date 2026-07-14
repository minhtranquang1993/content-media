---
name: content-media
description: >-
  Tạo content từ video/audio local hoặc URL YouTube/Shorts: lấy transcript (youtube-captions / Deepgram) → viết caption TikTok + title/description SEO YouTube + hashtag.
  Hỗ trợ doctor profile flag (profile-bstuan) để tạo thêm Facebook post cá nhân hóa theo giọng bác sĩ.
  Thêm chữ `ads` vào lệnh (chỉ brand DND) → chuyển sang ads mode: sinh Facebook Ads 3 variations chuẩn dnd-ads thay cho content social.
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

### Mode: social (mặc định) vs ads
Skill có 2 chế độ **loại trừ nhau**:
- **social** (mặc định, hoặc thêm chữ `social`): sinh content organic — TikTok / YouTube / Threads (+ FB post giọng bác sĩ nếu có profile flag). Workflow như cũ.
- **ads** (thêm chữ `ads`, CHỈ brand DND): sinh **Facebook Ads 3 variations** thay cho content social. KHÔNG xuất TikTok/YouTube/Threads.
- Không ghi gì → mặc định `social`. Lỡ ghi cả `social` lẫn `ads` → ưu tiên `ads`, báo nhẹ "đã bỏ qua social".
- Override loại ưu đãi trong ads mode: `ads=kx` / `ads=pc` / `ads=or` (nếu auto-detect sai).

Ví dụ: `/content-media https://youtube.com/... ads`
Ví dụ: `/content-media "C:\Users\Admin\Videos\mo-can.mp4" ads=kx`

### Doctor Profile Flag (optional, CHỈ social mode)
Thêm vào cuối lệnh để sinh Facebook post cá nhân hóa theo bác sĩ:
- `profile-bstuan` → BS Bùi Quang Tuấn (Giám đốc BV)

> ⚠️ Profile flag CHỈ có tác dụng ở social mode. Trong ads mode, cờ `profile-*` bị bỏ qua (báo nhẹ "profile chỉ dùng cho social").

Ví dụ: `/content-media https://youtube.com/... profile-bstuan`
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
  ├─ 4b. MODE ROUTER (parse cờ trong lệnh):
  │     ├─ có `ads` (hoặc `ads=kx|pc|or`) → MODE = ads
  │     ├─ có `social` HOẶC không cờ nào → MODE = social
  │     └─ có cả `social` lẫn `ads` → MODE = ads + báo nhẹ "đã bỏ qua social"
  │
  ├─ ══ NHÁNH social (MODE == social) ══
  │  ├─ 5. Viết caption TikTok — 2 VARIANTS:
  │  │     ├─ short_hook: hook mạnh, max 150 ký tự (dùng làm caption khi đăng)
  │  │     └─ full_caption: hook + body + CTA + hashtag, 400-900 ký tự (max 2200)
  │  ├─ 6. Viết title YouTube SEO
  │  ├─ 7. Viết description YouTube SEO
  │  ├─ 8. Viết Threads post (max 500 ký tự, casual, hook-first)
  │  ├─ 8b. Hashtag enforcement (best-effort, prompt-level):
  │  │     ├─ Đọc brand từ brand_profiles.md → lấy `required_hashtags[brand]`
  │  │     ├─ Merge required_hashtags vào output NON-exempt:
  │  │     │  → TikTok full_caption + YouTube description + Threads post
  │  │     ├─ Exemptions (3 loại):
  │  │     │  1. Doctor voice FB post (Step 9)
  │  │     │  2. TikTok short_hook (≤150 chars, ưu tiên #dnd + #dndsaigon nếu vừa)
  │  │     │  3. Sensitive posts (cảnh báo bệnh, tin buồn) — 0-2 tag manual
  │  │     └─ Dedupe hashtag list trước khi trả output
  │  ├─ 9. [Nếu có profile flag] Viết Facebook post theo voice bác sĩ
  │  │     ├─ profile-bstuan → giọng BS Bùi Quang Tuấn (chuyên môn sâu, quyết đoán)
  │  │     ├─ Xem persona & guidelines: references/doctor_profiles.md
  │  │     ├─ Doctor voice EXCEPTION: KHÔNG áp 4 hashtag mandatory DND vào FB post BS
  │  │     ├─ Chỉ dùng 2-3 hashtag từ personal pool BS (xem doctor_profiles.md)
  │  │     └─ Không tag bệnh viện trực tiếp
  │  └─ 10. Trả anh duyệt
  │
  └─ ══ NHÁNH ads (MODE == ads) — CHỈ Facebook, CHỈ tiếng Việt ══
     ├─ A1. Guard scope: user đòi platform khác FB → báo "ads chỉ hỗ trợ Facebook";
     │       đòi lang=en/tiếng Anh → báo "ads chỉ tiếng Việt". Không cố sinh.
     ├─ A2. Brand gate (3 tầng — quyết định có mở khóa fact DND):
     │     ├─ tín hiệu Thành Hưng (logistics/chuyển nhà) → SKIP ads,
     │     │   báo "Thành Hưng không chạy ads" (KHÔNG fallback sang social)
     │     ├─ Confirmed DND (y tế mắt rõ: mổ cận/SMILE/phaco/ortho-k/tên BS DND/"DND")
     │     │   → proceed ĐẦY ĐỦ: mở khóa dnd_info.md + ads_promotions.md
     │     └─ Ambiguous (không tín hiệu nào) → cảnh báo "đang giả định DND — dừng
     │         nếu sai", proceed NHƯNG KHÓA fact DND: chỉ dùng thông tin trong
     │         transcript/desc; thiếu quá → note user xác nhận brand, KHÔNG bịa
     ├─ A3. Auto-detect loại dịch vụ từ transcript → kx/pc/or (override `ads=`);
     │       không rõ → no-offer fallback (giữ 4 phần, "Ưu đãi" = benefit trung tính)
     ├─ A4. Bác sĩ: CHỈ nhắc khi transcript/input nêu rõ tên (match từ khóa nhận
     │       diện trong dnd_info.md) → đưa ngôi thứ 3. KHÔNG detect được → dùng copy
     │       cấp cơ sở/dịch vụ, TUYỆT ĐỐI KHÔNG tự kéo tên/credentials bác sĩ bất kỳ
     │       từ dnd_info.md để lấp chỗ. Bỏ qua cờ profile-* → báo nhẹ.
     ├─ A5. Đọc source THEO TẦNG brand (tránh leak fact DND ở Ambiguous):
     │     ├─ Confirmed DND → đọc facebook_ads.md + ads_promotions.md + dnd_info.md
     │     └─ Ambiguous → CHỈ đọc facebook_ads.md (rule file) + transcript/desc;
     │         TUYỆT ĐỐI KHÔNG nạp ads_promotions.md lẫn dnd_info.md
     ├─ A6. Sinh 3 variations theo bố cục 4 phần (Hook→Nội dung→Ưu đãi→CTA + Headline + Description)
     ├─ A7. QA nặng (BẮT BUỘC): validate_chars.py đếm ký tự (mapping 9 item, so tay
     │       125/40/30) → persona QA 5 persona forced-defect → scoring 1-10,
     │       avg ≤6 → viết lại
     └─ A8. Output theo Output Contract ads (facebook_ads.md) — KHÔNG hashtag,
             KHÔNG xuất TikTok/YouTube/Threads. Trả anh duyệt.
```

## ⚠️ Context Safety Rules

1. **KHÔNG BAO GIỜ** đọc toàn bộ raw transcript > 12k chars vào context cùng lúc
2. Transcript dài → đọc chunk → tóm tắt → discard → đọc chunk tiếp
3. Viết content từ **summary**, không từ raw transcript dài
4. Video > 60 phút → cảnh báo anh trước khi làm

## References
- `references/style-dimensions-power-words.md` — Style Dimensions (TikTok caption profile) + Power Words tiếng Việt
- `references/brand_profiles.md` — Brand profiles, hashtag pool, content guidelines
- `references/doctor_profiles.md` — Doctor persona: BS Tuấn (profile-bstuan). Dùng khi có doctor profile flag (social mode).
- `references/facebook_ads.md` — [ads mode] Bố cục FB ads, char budget, hook types, CTA, từ cấm, QA nặng, output contract.
- `references/ads_promotions.md` — [ads mode] Ưu đãi DND theo kx/pc/or (maintain độc lập với dnd-ads).
- `references/dnd_info.md` — [ads mode] Info công ty + credentials bác sĩ ngôi 3 (nguồn sự thật cho QA).

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

**Trước tiên xác định MODE (xem Mode Router / 4b):**
- `MODE == ads` → BỎ QUA phần social bên dưới; theo nhánh ads (A1-A8) + `references/facebook_ads.md`.
- `MODE == social` → viết các output social dưới đây.

#### Social mode
Đọc transcript từ output file (`--output`), xác định brand (xem `references/brand_profiles.md`), rồi viết:
1. **Caption TikTok — short_hook** — hook mạnh, max 150 ký tự, 2-3 hashtag, 1-2 emoji
2. **Caption TikTok — full_caption** — hook + body + CTA, 400-900 ký tự (max 2200), 5 hashtag
3. **Title YouTube** — có keyword chính, max 70 ký tự
4. **Description YouTube** — 300-500 từ, chuẩn SEO, có CTA + thông tin liên hệ + hashtag
5. **Threads post** — max 500 ký tự, casual tone, hook-first, không cần link preview
6. **[Optional] Facebook post (BS)** — nếu có `profile-bstuan`:
   - Đọc persona từ `references/doctor_profiles.md`
   - Viết 200-380 ký tự, ngôi thứ nhất, theo voice bác sĩ tương ứng
   - Chọn 1 điểm nổi bật từ video, diễn giải qua lăng kính chuyên môn của BS
   - 2-3 hashtag cuối (không link, không tag bệnh viện trực tiếp)
   - Hashtag pool riêng của BS. KHÔNG merge với `required_hashtags[dnd]`.

#### Hashtag mandatory check (brand DND, CHỈ social mode)
4 tag `#dnd #dndsaigon #benhvienmat #benhviendnd` PHẢI có ở TikTok full_caption + YouTube description + Threads post. TikTok short_hook (≤150 ký tự): ưu tiên `#dnd + #dndsaigon` nếu đủ chỗ; nếu không, chọn 1-2 tag phù hợp nhất — không phải ép cả 4 tag. Brand Thành Hưng: `required_hashtags` = `[]`, tuyệt đối không chèn tag DND. **Ads mode KHÔNG áp quy tắc hashtag này — ads không gắn hashtag.**

## Notes
- Cookies file: `.claude\credentials\yt_cookies.txt` (cho yt-dlp fallback, nếu có)
- Deepgram key trong `credentials/yt_content_secrets.json`
- Brand profiles + hashtag pool: `references/brand_profiles.md`
- Output mặc định: private draft → anh duyệt → public
- **KHÔNG lưu audio/video trong workspace** — chỉ dùng system tempdir (`tempfile.gettempdir()`), tự cleanup

## Output Contract

> Ads và social **loại trừ nhau** — không bao giờ xuất đồng thời cả hai bộ output.

### A) MODE == social (Tier-2, như cũ)

**Output bắt buộc (luôn có):**
- Transcript status: success/fallback/cache/fail + nguồn (cache/youtube-captions/deepgram)
- TikTok short_hook (≤150 ký tự)
- TikTok full_caption (400-900 ký tự, max 2200)
- YouTube title
- YouTube description
- Threads post (≤500 ký tự)
- Hashtag set

**Output optional (chỉ khi có doctor profile flag):**
- `profile-bstuan` → **Facebook post — Góc nhìn BS Tuấn** (200-380 ký tự, ngôi thứ nhất, tone chuyên môn)

**Definition of Done (social):**
- Có đủ 6 output bắt buộc kể cả khi transcript dùng fallback
- Nếu có doctor profile flag: có thêm Facebook post theo đúng persona
- Nếu transcript fail hoàn toàn: phải báo rõ lý do + phương án xử lý
- Brand DND (non-doctor): 4 hashtag mandatory PHẢI xuất hiện ở YouTube description + Threads + TikTok full_caption
- TikTok short_hook (exempt): chứa 1-2 tag ưu tiên `#dnd/#dndsaigon` nếu vừa char cap
- Brand Thành Hưng: KHÔNG chứa hashtag DND ở bất kỳ output nào
- Doctor voice FB post: KHÔNG chứa 4 tag DND mandatory

### B) MODE == ads (brand Confirmed DND / Ambiguous-đã-cảnh-báo)

Dùng **Output Contract ads** trong `references/facebook_ads.md` — THAY THẾ HOÀN TOÀN output social:
- Campaign info + 3 variations (Hook/Nội dung/Ưu đãi/CTA/Headline/Description) + Gợi ý A/B Test + Conversation Starters + QA Report
- KHÔNG xuất TikTok/YouTube/Threads. KHÔNG gắn hashtag.

**Definition of Done (ads):**
- Đúng 3 variations, mỗi variation đủ 4 phần + Headline + Description
- Char OK: Hook ≤125, Headline ≤40, Description ≤30 — xác định **thủ công** từ cột `chars` của validate_chars.py (KHÔNG dùng cột `pass` của script — đó là limit Google, không áp cho FB)
- Persona QA 5 persona đã chạy (mỗi persona có evidence), average score > 6
- Ưu đãi/bác sĩ khớp nguồn (`ads_promotions.md` / `dnd_info.md`); tầng Ambiguous KHÔNG chứa fact DND

### C) MODE == ads && brand == Thành Hưng (skip)

- Chỉ 1 dòng báo: "Thành Hưng không chạy ads, đã bỏ qua." KHÔNG xuất ads, KHÔNG fallback sang social.

## Category
content-seo
