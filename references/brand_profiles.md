# Brand Profiles — yt-content skill

## DND Sài Gòn (default)
- **Tên brand:** Bệnh viện Mắt Quốc tế DND Sài Gòn
- **Website:** matquoctednd.vn
- **Địa chỉ:** 147-147B-147 Bis Trương Định, Phường Nhiêu Lộc, TP.HCM
- **Hotline:** [cập nhật khi có]
- **Lĩnh vực:** Y tế mắt (LASIK, khúc xạ, phẫu thuật mắt, khám mắt)
- **Audience:** Người 18-40 tuổi bị cận thị, muốn phẫu thuật mắt

## Thành Hưng (SEO/content side project)
- **Tên brand:** Thành Hưng
- **Lĩnh vực:** Vận chuyển nhà/văn phòng
- **Website:** chuyennhathanhhung.vn

## ASR Glossary — sửa lỗi transcript (tên riêng + thuật ngữ)

Transcript từ ASR (youtube-captions / Deepgram) hay nghe nhầm tên riêng và
thuật ngữ y khoa. Dùng glossary này làm **ngữ cảnh cho Claude tự sửa** khi viết
content — KHÔNG regex thay thế mù. Nếu transcript có từ nghe gần giống mục bên
trái, sửa về dạng chuẩn bên phải.

### Tên riêng (brand + bác sĩ)
- Bệnh viện Mắt Quốc tế DND Sài Gòn (biến thể sai ASR: "đê en đê", "d and d", "dnd sài gòn", "đi ơn đi")
- BS Bùi Quang Tuấn (sai: "bùi quang tuấn", "quang tuấn", "bác tuấn")
- matquoctednd.vn (sai: "mắt quốc tế dnd chấm vn")

### Thuật ngữ mắt (chuẩn hoá chính tả)
- cận thị · loạn thị · viễn thị · lão thị
- LASIK (sai: "lê sịt", "la sịt", "lasic") · Femto LASIK · SMILE · Relex Smile
- Phakic / Phakic ICL (sai: "pha kích", "phaic", "pha kic")
- Phaco (sai: "pha cô", "pha co") · đục thủy tinh thể
- khúc xạ · độ cận · kính áp tròng · Ortho-K (sai: "otho ka", "orto k")
- võng mạc · dịch kính · đáy mắt · giác mạc · thủy tinh thể
- nhược thị · khô mắt · tăng nhãn áp / glaucoma

> Brand Thành Hưng (vận chuyển): glossary trên KHÔNG áp dụng. Chỉ chuẩn hoá tên
> "Thành Hưng" và địa danh nếu nghe nhầm.

## Required Hashtags (per-brand mandatory)

Mandatory tag set MUST xuất hiện trong mọi output (TikTok short_hook, TikTok
full_caption, YouTube description, Threads post) trừ khi rơi vào exception
list (xem SKILL.md workflow → hashtag enforcement).

```yaml
required_hashtags:
  dnd:
    - "#dnd"
    - "#dndsaigon"
    - "#benhvienmat"
    - "#benhviendnd"
  thanh_hung: []
```

## Hashtag pool theo lĩnh vực

### Y tế mắt
TikTok: #LASIK #PhẫuThuậtMắt #KhámMắt #CậnThị #MắtDND #SứcKhoẻMắt #BệnhViệnMắt #LaserMắt #MắtQuốcTếDND #TpHCM
YouTube: #LASIK #PhẫuThuậtMắt #KhámMắt #CậnThị #MắtQuốcTếDND #DNDSàiGòn #LaserMắt #SứcKhoẻMắt #BệnhViệnMắt #TpHCM #EyeCare #VisionCorrection #CorrectiveEyeSurgery

### Vận chuyển
TikTok: #ChuyểnNhà #VậnChuyển #ChuyểnVănPhòng #ThànhHưng #ChuyểnNhàTpHCM
YouTube: #ChuyểnNhà #VậnChuyểnNhà #ChuyểnVănPhòng #ThànhHưng #DịchVụChuyểnNhà #TpHCM

## Content guidelines

### Caption TikTok — short_hook
- Max 150 ký tự (dùng làm caption chính khi đăng)
- Hook mạnh đầu câu (câu hỏi, số liệu, reveal)
- 2-3 hashtag phù hợp
- 1-2 emoji

### Caption TikTok — full_caption
- 400-900 ký tự (max 2200 theo giới hạn TikTok thực tế)
- Hook (2 dòng) + Body (3-5 điểm chính) + CTA + 5 hashtag
- Emoji vừa đủ (4-6 cái)
- CTA cuối rõ ràng (đặt lịch / xem thêm / bình luận)

### Title YouTube SEO
- Max 70 ký tự
- Có keyword chính ở đầu hoặc giữa
- Tránh clickbait quá lố
- Format hay dùng: "[Keyword chính] - [Benefit/Hook] | [Brand]"

### Description YouTube SEO
- 300-500 từ
- Đoạn 1 (2-3 câu): tóm tắt nội dung + keyword chính
- Đoạn 2: bullet points nội dung chính (✅ icon)
- Đoạn 3: CTA + thông tin liên hệ brand
- Cuối: 10-15 hashtag
- Keyword density: tự nhiên, không spam

### Threads post
- Max 500 ký tự
- Casual, conversational — viết như chia sᮣ với bạn bè
- Hook-first: câu đầu phải cuốn người dùng tiếp tục đọc
- Không cần lính nước / link preview — viết đủ ý trong text
- 2-3 hashtag nhẹ, emoji nhẹ (1-3 cái)
- Tone: thực tế, chân thật, đồng cảm với reader
