# Facebook Ads — content-media (ads mode, DND)

> Module tự chứa cho **ads mode** của content-media. Chỉ sinh khi lệnh có chữ `ads` và brand là DND.
> Bố cục 4 phần: Hook → Nội dung chính → Ưu đãi → CTA.

---

## Scope cứng (không vượt)

- **Output language: CHỈ tiếng Việt.** Ads mode không hỗ trợ `lang=en`. User yêu cầu tiếng Anh → báo (bằng tiếng Việt, ngắn gọn): "Ads mode chỉ hỗ trợ tiếng Việt."
- **Platform: CHỈ Facebook.** Không Google RSA / TikTok ads / đa nền tảng. User yêu cầu platform khác → báo: "Ads mode chỉ hỗ trợ Facebook. Google RSA dùng skill /dnd-ads."
- **Brand: CHỈ DND.** Xem "Brand gate" trong SKILL.md nhánh ads.

> ⚠️ **Nạp source theo tầng brand (chống leak fact DND):**
> - **Confirmed DND** → được đọc file này + `ads_promotions.md` + `dnd_info.md`.
> - **Ambiguous** (đã cảnh báo) → CHỈ đọc file này + transcript/desc. TUYỆT ĐỐI KHÔNG nạp `ads_promotions.md` lẫn `dnd_info.md` (không số ca, không tên/credentials bác sĩ, không ưu đãi, không USP DND).

---

## Char budget (visible)

| Element | Limit visible | Lý do |
|---------|:-------------:|-------|
| **Hook (primary text)** | **≤ 125 ký tự** trước "Xem thêm" | Mobile truncate sau 125 |
| **Headline** | **≤ 40 ký tự** | Bị cắt trên mobile |
| **Description** | **≤ 30 ký tự** | Không hiện mọi placement |

- 95%+ user xem trên mobile → câu ngắn, xuống dòng nhiều, emoji tiết chế (1-3).

---

## Bố cục 4 phần (bắt buộc, mọi variation)

### Phần 1: 🪝 Hook (8-10 từ)
- Ngắn, gây chú ý ngay, nằm trong 125 ký tự đầu.
- KHÔNG tiêu cực (sợ mù, hối hận, dọa). KHÔNG nhân xưng — thiếu chủ ngữ hoặc passive.

**Hook types ưu tiên:**

| Loại | Ví dụ | Khi nào dùng |
|------|-------|-------------|
| Pattern Interrupt | "8 giây — và mắt sáng lại từ đây" | Video SMILE Pro |
| Curiosity/Open Loop | "Lý do 10.000 người chọn bỏ kính tại đây" | General awareness |
| Future Pacing | "Tưởng tượng sáng mai mở mắt — không cần kính" | Emotional |
| Social Proof + Số | "300.000 ca thành công — câu chuyện tiếp theo là..." | Authority |
| Micro-Question | "Cận 5 độ — mổ hay đeo kính cả đời?" | Engagement |
| Benefit-First | "Bỏ kính chỉ 15 phút — không đau, phục hồi 24h" | Direct benefit |

**Hook cấm:** "Đừng để mắt hỏng mới hối hận" (tiêu cực) · "Bạn có biết cận thị nguy hiểm..." (dọa) · "Chúng tôi là bệnh viện hàng đầu" (nhân xưng + tự khen) · "Anh/chị đang bị cận?" (nhân xưng).

### Phần 2: 📝 Nội dung chính (3-5 câu)
- Tóm tắt ý chính từ transcript video/ảnh/desc.
- **Bác sĩ (ngôi thứ 3, chỉ Confirmed DND)**: CHỈ nhắc bác sĩ khi transcript/desc/user input **nêu rõ tên bác sĩ đó**. Khi đó đưa vào ngôi thứ 3 như social proof — "BSNT Bùi Quang Tuấn — 13+ năm, hàng chục nghìn ca", lấy credentials từ `dnd_info.md`.
  - ⛔ **KHÔNG detect được bác sĩ trong transcript/input → TUYỆT ĐỐI KHÔNG tự chọn/gán một bác sĩ bất kỳ từ `dnd_info.md` để "lấp chỗ".** Thay bằng copy cấp cơ sở/dịch vụ (không tên người). Gán nhầm bác sĩ = lỗi accuracy/compliance nghiêm trọng.
  - KHÔNG viết giọng bác sĩ ngôi 1 (đó là social mode).
- Thiếu chủ ngữ, câu ngắn, xuống dòng.

### Phần 3: 🎁 Ưu đãi
- Nguồn phụ thuộc brand gate + service detect:
  - **Confirmed DND + detect được dịch vụ** (kx/pc/or): copy nội dung từ `ads_promotions.md` section tương ứng. Format bullet, giữ emoji ✨🔥.
  - **Confirmed DND + KHÔNG detect được dịch vụ** (no-offer fallback): KHÔNG bịa số/%/tên ưu đãi. Thay bằng **benefit trung tính cấp brand** từ `dnd_info.md` (VD: "Miễn phí tái khám & đồng hành hậu phẫu 3 năm", "Khám chuyên sâu 12 bước"). KHÔNG lấy fact chỉ đúng cho 1 gói dịch vụ hẹp.
  - **Ambiguous brand**: KHÔNG dùng `ads_promotions.md` lẫn `dnd_info.md`. Chỉ nêu giá trị chung có trong transcript/desc, hoặc để CTA mềm gánh (bỏ khối ưu đãi số liệu).

### Phần 4: 📣 CTA
- Action cụ thể + lợi ích, thiếu chủ ngữ.

**CTA templates:**

| Loại | CTA gợi ý |
|------|-----------|
| kx | "NHẮN TIN đặt lịch khám miễn phí + nhận ưu đãi mổ cận tháng 7 🔥" |
| kx | "💬 Inbox ngay — Khám 12 bước miễn phí, tư vấn phương pháp phù hợp" |
| pc | "NHẮN TIN đặt lịch khám miễn phí + nhận ưu đãi Femto Phaco 30% 🎁" |
| pc | "💬 Inbox — Tư vấn chi tiết về phẫu thuật đục thủy tinh thể" |
| or | "NHẮN TIN đặt lịch khám mắt miễn phí cho bé + ưu đãi Ortho-K tháng 7" |
| Mềm (no-offer / ambiguous) | "💬 Inbox đặt lịch khám — được tư vấn phương pháp phù hợp" |

---

## Tone & Writing Rules

- **Formal level 7/10** — chuyên nghiệp nhưng gần gũi, thiếu chủ ngữ là phong cách chính.
- **Nhân xưng: KHÔNG DÙNG** "chúng tôi", "chúng mình", "anh/chị", "bạn". Dùng thiếu chủ ngữ / passive / tên cụ thể ("Bệnh viện Mắt DND Sài Gòn", "DND").
- **Emotional range:** ✅ an tâm, tin tưởng, hy vọng, quyết tâm, empathy. ❌ bi kịch, panic, aggressive, dọa.
- **Emoji:** tối đa 1-3 cho toàn primary text. Dùng 👁️ 🔬 ✨ 🎁 💬. Không spam kiểu ecommerce.

### Từ cấm
```
"mua ngay", "deal sốc", "sale sập sàn", "giá rẻ"
"100% thành công", "chắc chắn khỏi", "cam kết khỏi bệnh"
"anh/chị", "bạn", "chúng tôi", "chúng mình"
"miễn phí" lặp > 2 lần
"shock", "điên", "khủng", "nhanh tay", "chớp ngay"
```

### Compliance y tế
- ❌ Không claim tuyệt đối ("100% thành công", "chắc chắn khỏi").
- ❌ Không nội dung gây sợ hãi, bi kịch.
- ✅ Disclaimer nhẹ nếu claim kết quả: "* Kết quả phụ thuộc vào tình trạng mắt và cơ địa từng người".

---

## QA (BẮT BUỘC — chạy trước khi output)

QA Flow: `1 generate → 2 char count → 3 persona QA → 4 sửa → 5 char count lại → 6 output`.

### Char QA — dùng `validate_chars.py` làm MÁY ĐẾM
`scripts/validate_chars.py` hardcode hard limit Google (30/90/15) nên **cột `pass` KHÔNG áp dụng cho Facebook — bỏ qua nó**. Script CHỈ dùng để đếm ký tự chính xác (cột `chars`, NFC — quan trọng với tiếng Việt có dấu).

**Field mapping (thứ tự cố định 9 item):** đưa vào field `titles` theo đúng thứ tự để đối chiếu không nhầm:
```
[V1 Hook, V1 Headline, V1 Description,
 V2 Hook, V2 Headline, V2 Description,
 V3 Hook, V3 Headline, V3 Description]   (index 1-9)
```
Chạy:
```bash
echo '{"titles":["...9 item đúng thứ tự..."]}' | python scripts/validate_chars.py
```
Đọc cột `chars` từng item, **so tay**:
- Hook (item 1, 4, 7) ≤ **125**
- Headline (item 2, 5, 8) ≤ **40**
- Description (item 3, 6, 9) ≤ **30**

Item nào lố → sửa, chạy lại. Hook đếm = phần primary text tính tới trước "Xem thêm" (áng theo 125).

> ⚠️ KHÔNG có bước "pass/fail tự động" cho Facebook. Quyết định đạt/không đạt char limit là **thủ công**, suy từ cột `chars` theo mapping 9 item ở trên. Cột `pass` và exit code của script (chuẩn Google 30/90/15) KHÔNG dùng để phán xét FB.

> Windows/Git Bash: dùng `python` (không phải `python3`). Nếu thiếu, thử `py -3`.

### Persona QA (Forced Defect Search) — 5 persona
Chạy tuần tự, TRONG CÙNG 1 lượt. Mỗi persona PHẢI chỉ ra ≥1 lỗi cụ thể ("Variation #{n}, câu '{quote}' — vi phạm vì {lý do}") HOẶC khai báo rõ đã check gì. Không được chỉ trả "OK".

| Persona | Trách nhiệm |
|---------|-------------|
| **Policy** | Chính sách quảng cáo Facebook y tế; không caps/ký tự đặc biệt quá mức |
| **Medical Claims** | Không claim tuyệt đối kết quả/phục hồi/an toàn; có disclaimer nếu cần |
| **Offer/Doctor Accuracy** | Ưu đãi khớp `ads_promotions.md`; bác sĩ khớp `dnd_info.md` (tên, chức danh, kinh nghiệm). Ở tầng Ambiguous: xác nhận KHÔNG có fact DND nào bị rút ra |
| **Mobile Scanability** | Hook ≤125, Headline ≤40, Description ≤30; câu ngắn, xuống dòng, preview OK mobile |
| **Brand/Tone** | Nhân xưng, từ cấm, formal 7/10, emoji ≤3 |

*(Không có persona "RSA Diversity" — đó chỉ dành cho Google RSA.)*

### Checklist cross-platform (rút gọn cho FB)
| # | Check |
|---|-------|
| C1 | Không claim tuyệt đối |
| C2 | Không từ cấm |
| C3 | Không nhân xưng |
| C4 | Ưu đãi khớp `ads_promotions.md` (nếu có dùng) |
| C5 | Bác sĩ khớp `dnd_info.md` (nếu có dùng) |
| C6 | CTA action cụ thể + lợi ích |
| C7 | Hook 8-10 từ, không tiêu cực, không nhân xưng |
| C8 | Emoji ≤ 3 |
| C9 | Tuân thủ healthcare ads FB |
| C10 | Disclaimer nếu claim kết quả |

### FB-specific
| # | Check |
|---|-------|
| F1 | Hook ≤ 125 ký tự |
| F2 | Headline ≤ 40 ký tự |
| F3 | Description ≤ 30 ký tự |
| F4 | 3 variations khác style/angle, không lặp cấu trúc |
| F5 | Mobile-first: câu ngắn, xuống dòng |

### Scoring (sau persona QA)
Score mỗi variation 1-10:

| Tiêu chí | Weight |
|----------|:------:|
| Hook gây chú ý & không tiêu cực | 25% |
| Nội dung chính relevant & compelling | 25% |
| Ưu đãi/giá trị rõ ràng | 20% |
| CTA mạnh, action cụ thể | 15% |
| Tone đúng (thiếu chủ ngữ, formal 7/10) | 15% |

- Score ≥ 8: output ngay · Score 7: output kèm gợi ý cải thiện · **Average ≤ 6: viết lại, KHÔNG output**.

---

## Output Contract — ads mode

```markdown
# 📱 Facebook Ads — DND {Dịch vụ}

## Thông tin chiến dịch
- **Ưu đãi:** {kx/pc/or — hoặc "no-offer fallback" / "ambiguous — chỉ dùng thông tin transcript"}
- **Material:** {video/ảnh/desc}
- **Bác sĩ:** {tên BS ngôi 3 nếu detect, hoặc "N/A"}
- **Brand tier:** {Confirmed DND / Ambiguous (đã cảnh báo)}

---

## Variation 1: {Tên style/angle}

### 🪝 Hook
{8-10 từ}

### 📝 Nội dung chính
{3-5 câu, bác sĩ ngôi 3 nếu có}

### 🎁 Ưu đãi
{từ ads_promotions.md / benefit trung tính / giá trị chung}

### 📣 CTA
{action + lợi ích}

### Headline
{≤ 40 ký tự}

### Description
{≤ 30 ký tự}

---

## Variation 2: {...}
## Variation 3: {...}

---

## 🧪 Gợi ý A/B Test
- **Hook:** {V1 vs V2 — lý do}
- **CTA:** {variation — lý do}
- **Visual:** {gợi ý creative từng variation}

## 💬 Conversation Starters (Messenger)
- "Muốn tìm hiểu về {dịch vụ}"
- "Cho hỏi giá {dịch vụ}"
- "Muốn đặt lịch khám"

---

## 🔍 QA Report
### Cross-Platform: {X}/10 passed
### Facebook-Specific: {X}/5 passed
### Char check (chars): V1 Hook {n}/125, Headline {n}/40, Desc {n}/30 · V2 ... · V3 ...
### Scores
- Variation 1: {score}/10
- Variation 2: {score}/10
- Variation 3: {score}/10
- **Average: {avg}/10** {✅ ≥7 | ❌ ≤6 → rewrite}
```

> ⚠️ ads mode THAY THẾ HOÀN TOÀN output social — KHÔNG xuất TikTok/YouTube/Threads. Ads và social loại trừ nhau. Ads mode KHÔNG gắn hashtag.
