# OmniLocal — QA Testing Checklist (Black-box)

> **Dự án:** OmniLocal — Hệ thống nội địa hóa sách thiếu nhi đa tác tử  
> **Đội ngũ:** APCS 24A01 · GDGoC 2026  
> **Bản quyền:** © 2026 Team APCS 24A01 — GDGoC 2026. All rights reserved.  
> **Phiên bản:** v1.0 · Tháng 4/2026  
> **File PDF test:** `test_cases/TestingBook.pdf` — 22 trang (Bìa + 10 chương × 2 trang)

---

## Hướng dẫn sử dụng

**Mục đích:** Tài liệu kiểm thử Hộp Đen (Black-box). Người kiểm thử **chỉ cần** đối chiếu giữa trang sách gốc và file PDF đầu ra cuối cùng của hệ thống để đánh dấu kết quả.

**Quy ước:**

| Ký hiệu | Ý nghĩa |
|:---:|---|
| **AC** | ✅ Accepted — Kết quả đúng hoàn toàn theo tiêu chí |
| **WA** | ❌ Wrong Answer — Kết quả sai hoặc vi phạm ràng buộc |

**Cách đánh dấu:** Đánh `[x]` vào ô AC hoặc WA. Ghi lý do cụ thể vào cột **Note** nếu WA.

---

## 🟢 PHASE 1 — PHÂN TÍCH YÊU CẦU DỰ ÁN (BRIEF PARSING)

> Kiểm tra: Hệ thống có đọc hiểu đúng file `brief.txt` của khách hàng và ánh xạ thành các constraint trong `global_metadata.json` hay không. Kết quả cuối cùng có tuân thủ Brief hay không.

---

### Test 1.1 — Nắm bắt độ tuổi độc giả

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3, đoạn 2 |
| **Brief (Input)** | *"Dịch sách cho trẻ em mầm non, dưới 6 tuổi"* |
| **Sách gốc (Input)** | `"He was very excited about today's adventure. He had been waiting for this moment his entire life — ever since his grandfather, the legendary warrior Steelfist, had told him stories about the ancient Kingdom beyond the mountains."` |
| **WA (Sai điển hình)** | Giữ nguyên giọng văn người lớn: *"Cậu ấy rất háo hức trước cuộc phiêu lưu hôm nay. Cậu đã chờ đợi khoảnh khắc này cả đời — kể từ khi ông nội..."* |
| **AC (Kết quả đúng)** | Giọng trẻ con vui nhộn: *"Cậu bé vui ơi là vui! Hôm nay đi chơi rồi! Từ hồi ông nội kể chuyện, cậu bé mê tít luôn á!"* |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 1.2 — Xử lý từ khóa nhạy cảm (Never Change Rules)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 6, đoạn 1 |
| **Brief (Input)** | *"Tuyệt đối cấm mọi từ ngữ mang tính bạo lực, đẫm máu"* |
| **Sách gốc (Input)** | `"He brutally killed the beast with his sword, slashing through the darkness like a bolt of lightning."` |
| **WA (Sai điển hình)** | *"Cậu ấy tàn nhẫn giết chết con quái thú bằng lưỡi kiếm, chém xuyên bóng tối như một tia sét."* |
| **AC (Kết quả đúng)** | *"Cậu ấy dũng cảm đánh bại con quái thú bằng thanh kiếm, lướt qua bóng tối nhanh như tia chớp."* — Né bạo lực, giữ nghĩa. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 1.3 — Bảo toàn nền tranh gốc (Bản quyền)
Test này skip, phase 4 có thể test test này. 
| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3, hình minh họa đầu trang — dòng chữ cloud-letters trên bầu trời |
| **Brief (Input)** | *"Tuyệt đối không được chỉnh sửa, vẽ lại bất kỳ hình minh họa gốc nào"* |
| **Sách gốc (Input)** | Hình: bầu trời xanh với chữ `"IT WAS A BEAUTIFUL DAY"` viết bằng cloud-letters. Prompt minh họa ghi rõ *"Large stylized text written across the blue sky in swirly white cloud-letters."* |
| **WA (Sai điển hình)** | AI chà xóa và vẽ lại đám mây phía sau chữ — phá hỏng nền tranh gốc (vi phạm bản quyền họa sĩ) |
| **AC (Kết quả đúng)** | Hình nền bầu trời giữ nguyên 100%. Hệ thống chỉ xóa chữ Anh, nhét chữ Việt lên trên. Nền mây trời không bị đụng chạm. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 1.4 — Kiểm soát thành ngữ (Translation Fidelity)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 22, đoạn 3 — Grandmother nói |
| **Brief (Input)** | *"Dịch sát nghĩa, trung thành với ý tác giả"* |
| **Sách gốc (Input)** | `"Old Mr. Henderson kicked the bucket last winter," she whispered sadly. "He was a kind man."` |
| **WA (Sai điển hình)** | *"Ông Henderson đá cái xô mùa đông năm ngoái."* — Dịch máy móc, mất nghĩa |
| **AC (Kết quả đúng)** | *"Ông Henderson đã qua đời mùa đông năm ngoái," bà thì thầm buồn bã.* — Giữ đúng nghĩa "qua đời" |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

## 🟡 PHASE 2 — DỊCH THUẬT VĂN CẢNH (TRANSLATION)

> Kiểm tra: Chất lượng bản dịch tiếng Việt — giọng văn, tính nhất quán, xử lý tên riêng, âm thanh, đại từ xuyên suốt cuốn sách.

---

### Test 2.1 — Giọng văn phù hợp lứa tuổi (Age Tone)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3, đoạn 3 — Ironfist thốt lên |
| **Constraint** | `target_age_tone: 16`, `style_register: "teen friendly"` |
| **Sách gốc (Input)** | `"Oh my God!" Ironfist shouted, looking at the dark clouds rolling in from the west like a stampede of angry grey horses.` |
| **WA (Sai điển hình)** | *"Ôi, thật bất ngờ! Ironfist thốt lên khi nhìn thấy đám mây đen ùn ùn kéo tới."* — Giọng cứng nhắc |
| **AC (Kết quả đúng)** | *"Trời ơi!" Ironfist la lên khi thấy mây đen kéo tới ào ào.* — Giọng teen tự nhiên, năng động |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.2 — Khóa tên nhân vật (Protected Names)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3, dòng đầu: `"Ironfist stepped out of his cottage"`. Xuất hiện mọi trang 3→22. |
| **Constraint** | `preserve_main_names: true`, `protected_names: ["Ironfist"]` |
| **Sách gốc (Input)** | `"Ironfist stepped out of his cottage and squinted against the morning sun."` (trang 3) |
| **WA (Sai điển hình)** | *"Quả Đấm Sắt bước ra khỏi nhà."* — Dịch tên riêng |
| **AC (Kết quả đúng)** | *"Ironfist bước ra khỏi nhà và nheo mắt nhìn ánh nắng ban mai."* — Giữ nguyên "Ironfist" |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.3 — Bản địa hóa Âm thanh SFX (Translate Mode)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 18, giữa trang — SFX lớn `MEOW!` |
| **Constraint** | `sfx_handling: "translate"` |
| **Sách gốc (Input)** | Chữ SFX `"MEOW!"` viết to, font nghệ thuật, đứng độc lập giữa đoạn văn (sau khi mèo kêu) |
| **WA (Sai điển hình)** | Giữ nguyên "MEOW!" hoặc dịch bằng font thường: "Tiếng mèo kêu" |
| **AC (Kết quả đúng)** | Thay bằng `"MEOOO!"` hoặc SFX Việt tương đương, font nghệ thuật giữ nguyên kích cỡ + vị trí |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.4 — Cấm dịch Âm thanh SFX (Keep Mode)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 12, giữa trang — SFX lớn `BOOM!` (sau đoạn pháo hoa) |
| **Constraint** | `sfx_handling: "keep_original"` |
| **Sách gốc (Input)** | Chữ SFX `"BOOM!"` viết to, font đậm, đứng riêng giữa trang (pháo hoa nổ ngoài cửa sổ) |
| **WA (Sai điển hình)** | AI tự ý dịch thành "BÙÙM!" hoặc xóa mất |
| **AC (Kết quả đúng)** | `"BOOM!"` giữ nguyên vẹn, không chỉnh sửa |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.5 — Bảo toàn định dạng nhấn mạnh (Bold / Italic)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3, đoạn 2 — câu `"He was very excited"` |
| **Sách gốc (Input)** | `"He was` ***very*** `excited about today's adventure."` — Chữ "very" in đậm nghiêng |
| **WA (Sai điển hình)** | *"Cậu ấy rất háo hức"* — Chữ "rất" không giữ định dạng in đậm/nghiêng |
| **AC (Kết quả đúng)** | *"Cậu ấy* ***rất*** *háo hức cho chuyến phiêu lưu hôm nay."* — Chữ "rất" giữ in đậm nghiêng |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.6 — Nhất quán danh từ xuyên suốt (Glossary Consistency)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 5: `"a Goblin leaped out"` → Trang 20: `"Another Goblin!"` |
| **Constraint** | `glossary_strict_mode: true` |
| **Sách gốc (Input)** | **Trang 5, đoạn cuối:** `"Suddenly, a Goblin leaped out from behind a twisted oak!"` **Trang 20, đoạn 1:** `"Another Goblin! But this one seemed different..."` |
| **WA (Sai điển hình)** | Trang 5: *"Yêu tinh"* → Trang 20: *"Quỷ lùn"* — Mỗi trang gọi một kiểu |
| **AC (Kết quả đúng)** | Cả trang 5 và trang 20 đều gọi thống nhất: *"Yêu tinh"* |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.7 — Bộ lọc Tôn Giáo / Chính trị

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3, đoạn 3 — Ironfist thốt lên |
| **Constraint** | `never_change_rules: ["Không dùng từ ngữ mang yếu tố tôn giáo"]` |
| **Sách gốc (Input)** | `"Oh my God!" Ironfist shouted, looking at the dark clouds rolling in from the west` |
| **WA (Sai điển hình)** | *"Ôi Chúa ơi!" Ironfist hét lên...* — Dùng từ tôn giáo |
| **AC (Kết quả đúng)** | *"Trời ơi!" Ironfist hét lên khi thấy mây đen kéo tới...* — Né tôn giáo |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.8 — Dịch thoát ý thành ngữ (Transcreation)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3, đoạn 3 — Ironfist nói tiếp |
| **Constraint** | `translation_fidelity: "transcreation"` |
| **Sách gốc (Input)** | `"It's raining cats and dogs already! I haven't even left the garden yet!"` |
| **WA (Sai điển hình)** | *"Trời đang mưa chó với mèo rồi! Tớ còn chưa ra khỏi vườn!"* — Dịch sống sượng |
| **AC (Kết quả đúng)** | *"Trời mưa to như trút nước rồi! Tớ còn chưa ra khỏi vườn nữa kìa!"* — Thành ngữ Việt |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.9 — Xưng hô liên chương (Coreference Consistency)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 13, đoạn 2 → Trang 21, đoạn 2 (cách 8 trang) |
| **Sách gốc (Input)** | **Trang 13:** `"You should be careful," Ironfist warned his sister as they began the steep ascent.` **Trang 21:** `"I told you to be careful," said Ironfist, grinning at Lily.` |
| **WA (Sai điển hình)** | Trang 13: *"Em phải cẩn thận."* → Trang 21: *"Tôi đã bảo bạn cẩn thận."* — Nhảy xưng hô |
| **AC (Kết quả đúng)** | Trang 13: *"Em phải cẩn thận nhé."* → Trang 21: *"Anh đã bảo em cẩn thận rồi mà."* — Mạch Anh-Em xuyên suốt |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 2.10 — Đại từ phi giới tính (Gender-neutral Pronoun)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 9, đoạn 4 — câu in đậm đứng riêng biệt |
| **Sách gốc (Input)** | `"They are coming closer."` — Sau đoạn mô tả: *"a shape emerged — neither man nor woman, neither young nor old."* Đại từ "They" chỉ một thực thể duy nhất chưa rõ giới tính. |
| **WA (Sai điển hình)** | *"Anh ấy đang đến gần."* hoặc *"Cô ấy đang đến gần."* — Quy chụp giới tính |
| **AC (Kết quả đúng)** | *"Kẻ đó đang đến gần."* hoặc *"Bóng đen đang tiến lại gần."* — Giữ trung tính |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

## 🟠 PHASE 3 — BẢN ĐỊA HÓA VĂN HÓA & HIỆU ỨNG CÁNH BƯỚM (LOCALIZATION)

> Kiểm tra: Thực thể văn hóa phương Tây có được thay thế phù hợp Việt Nam không? Sự thay thế có **nhất quán xuyên suốt** cuốn sách (Butterfly Effect) không? Có phá vỡ logic cốt truyện không?

---

### Test 3.1 — Thay đổi văn hóa đồ ăn

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 11, đoạn 2 — kèm hình minh họa Turkey |
| **Constraint** | `cultural_localization: true` |
| **Sách gốc (Input)** | `"They enjoyed a big roasted Turkey for Christmas dinner. The golden bird sat at the center of the long oak table."` + Hình minh họa Turkey trên bàn tiệc |
| **WA (Sai điển hình)** | *"Cả nhà thưởng thức con Gà Tây nướng cho bữa tối Giáng sinh."* — Giữ nguyên văn hóa Tây |
| **AC (Kết quả đúng)** | *"Cả nhà quây quần bên mâm cỗ Tết có đĩa gà luộc lá chanh."* — Chuyển đổi phù hợp Việt Nam. Hình Turkey cũng được đánh dấu để Phase 4 vẽ lại. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.2 — Tính toán chuyển đổi Đơn vị Đo Lường

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 14, đoạn đầu — lời ông hướng dẫn viên |
| **Sách gốc (Input)** | `"Walk 15 miles to the North. Bring 3 pounds of dried food and plenty of water. It's nearly 100 degrees Fahrenheit out there in the sun, believe it or not."` |
| **WA (Sai điển hình)** | *"Đi bộ 15 miles về phía Bắc. Mang 3 pounds thức ăn khô. Ngoài trời gần 100 độ Fahrenheit."* — Giữ nguyên đơn vị |
| **WA (Sai điển hình 2)** | *"Đi bộ 15 dặm. Mang 3 cân thức ăn khô."* — Quy đổi sai (3 lbs ≠ 3 kg) |
| **AC (Kết quả đúng)** | *"Đi bộ khoảng 24 km về phía Bắc. Mang 1,4 ký thức ăn khô. Ngoài nắng gần 38 độ C."* — Quy đổi chính xác: 15 miles ≈ 24 km, 3 lbs ≈ 1.36 kg, 100°F ≈ 37.8°C |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.3 — Hiệu ứng Cánh Bướm Tương Lai (Forward Butterfly)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 7, đoạn 3 → Trang 22, đoạn 2 (cách 15 trang) |
| **Sách gốc (Input)** | **Trang 7:** `"He took the Subway downtown — the rumbling train carrying him through dark tunnels beneath the streets."` **Trang 22:** `"Ironfist remembered taking the Subway at the start of his journey — it felt like a lifetime ago."` |
| **WA (Sai điển hình)** | Trang 7 dịch "xe buýt" nhưng trang 22 vẫn dịch *"nhớ lại lúc đi tàu điện ngầm"* — Mâu thuẫn |
| **AC (Kết quả đúng)** | Trang 22 đồng bộ: *"Ironfist nhớ lúc đi xe buýt đầu hành trình"* — Khớp với trang 7 |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.4 — Hiệu ứng Cánh Bướm Quá Khứ (Backward Butterfly)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 8, đoạn 1 ↔ Trang 22, đoạn 2 (cách 14 trang) |
| **Sách gốc (Input)** | **Trang 8:** `"Outside the station, a group of children had built a Snowman. It wore a top hat and had a bright orange carrot for a nose."` **Trang 22:** `"The spot where children had built a Snowman was now bare, the snow melted away, leaving only a muddy circle..."` |
| **WA (Sai điển hình)** | Trang 22 dịch "Bù nhìn rơm" nhưng Trang 8 vẫn viết *"Người Tuyết"* — Mất đồng bộ |
| **AC (Kết quả đúng)** | Cả 2 trang đều dùng cùng một thuật ngữ: *"Bù nhìn rơm"* (hoặc cùng *"Người Tuyết"*) — Nhất quán |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.5 — Logic vật lý hành động (Physical Action Consistency)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 17, đoạn cuối — cô tiên rút Wand |
| **Sách gốc (Input)** | `"She pulled out her Wand — long, thin, and shimmering like a sliver of captured starlight — and carefully inserted it into the tiny keyhole. The Wand fit perfectly, its slender form sliding into the narrow opening."` |
| **WA (Sai điển hình)** | Bản địa hóa "Wand" thành "Quả cầu thần kỳ" — Hình cầu tròn không thể chọc vào lỗ khóa hẹp |
| **AC (Kết quả đúng)** | Giữ "Đũa phép" hoặc đổi thành vật thon dài (VD: *"Cây bút thần"*). Hành động "chọc vào lỗ khóa" vẫn hợp lý vật lý. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.6 — Cải biên môn thể thao văn hóa

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 19, đoạn 3 — bọn trẻ hét |
| **Constraint** | `cultural_localization: true` |
| **Sách gốc (Input)** | `"Let's play baseball after school!" shouted a group of children running across the green field with bats and gloves.` + Hình minh họa trẻ chơi Baseball |
| **WA (Sai điển hình)** | *"Chúng mình chơi bóng chày sau giờ học nhé!"* — Bóng chày không phổ biến ở VN |
| **AC (Kết quả đúng)** | *"Chúng mình chơi đá bóng sau giờ học nhé!"* + Hình minh họa cũng được đánh dấu để Phase 4 vẽ lại. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.7 — Bản địa hóa địa danh / Địa lý

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 13, đoạn 1 — mở đầu chương |
| **Sách gốc (Input)** | `"Ironfist and his little sister Lily set out for the Rocky Mountains."` |
| **WA (Sai điển hình)** | *"Ironfist và em gái Lily lên đường đến Núi Rocky."* — Giữ nguyên địa danh Tây |
| **AC (Kết quả đúng)** | *"Ironfist và em gái Lily lên đường đến đỉnh Fansipan."* — Địa danh núi VN tương đương (cao, lạnh) |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.8 — Cấm giải thích dư thừa (Over-Explain)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 15, đoạn 3 — Ironfist kể câu đố |
| **Sách gốc (Input)** | `"Time flies like an arrow; fruit flies like a banana!"` — Ironfist nói với Lily bên lửa trại |
| **WA (Sai điển hình)** | *"Thời gian bay như mũi tên; ruồi trái cây thì thích chuối. (Lưu ý: đây là chơi chữ vì 'flies' vừa nghĩa 'bay' vừa nghĩa 'ruồi')"* — AI nhét giải thích |
| **AC (Kết quả đúng)** | *"Thời gian vun vút như tên bay, còn lũ ruồi thì chuộng miếng chuối chín!"* — Gọn, hài hước, không giải thích |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.9 — Đồng bộ Biển Hiệu (Signboard) với Hội Thoại

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 12, đoạn 1 (biển hiệu) → Trang 21, đoạn 3 (hội thoại). Cách 9 trang. |
| **Sách gốc (Input)** | **Trang 12:** `"On the wall behind the head table hung a wooden signboard that read 'BAKERY' in ornate golden letters."` **Trang 21:** `"Did you enjoy the Bakery we visited?" asked Lily. "The one with the golden sign?"` |
| **WA (Sai điển hình)** | Trang 12 dịch biển: *"Tiệm Bánh"* nhưng trang 21 dịch: *"Tớ thích cửa hàng tạp hóa"* — Mất liên kết |
| **AC (Kết quả đúng)** | Trang 12: *"Tiệm Bánh"*. Trang 21: *"Em có thích Tiệm Bánh mình ghé không?"* — Đồng bộ |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 3.10 — Giữ chân bối cảnh khi Brief yêu cầu (No Cultural Drift)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 19, đoạn 4 — mô tả cảnh phố |
| **Constraint** | `cultural_localization: false` (Brief yêu cầu giữ nguyên phương Tây) |
| **Sách gốc (Input)** | `"a red double-decker bus rumbled down the cobblestone street... An old red telephone booth stood on the corner like a silent guardian from another era."` + Hình minh họa xe bus đỏ London + bốt điện thoại đỏ |
| **WA (Sai điển hình)** | AI tự ý bản địa hóa: thay xe bus bằng xe máy, bốt điện thoại bằng trụ đèn giao thông |
| **AC (Kết quả đúng)** | Giữ nguyên: *"chiếc xe bus hai tầng màu đỏ... bốt điện thoại đỏ đứng ở góc phố"*. Chỉ dịch chữ. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

## 🔵 PHASE 4 — TÁI TẠO HÌNH ẢNH & CHÈN CHỮ (VISUAL RECONSTRUCTION)

> Kiểm tra: Hình nền có bị phá nát không? Vật thể bản địa hóa có được vẽ thay thế đúng chỗ không? Chữ tiếng Việt có nằm vừa vặn trong khung thoại không?

---

### Test 4.1 — Tráo Vật Thể Bản Địa Hóa (Object Swap)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 11, đoạn cuối — Ironfist cầm Hamburger |
| **Sách gốc (Input)** | Hình minh họa Ironfist cầm Hamburger trên tay tại bàn tiệc. Text đổi thành "Bánh Chưng" (theo Phase 3). |
| **WA (Sai điển hình)** | (1) Tay nhân vật bị cắt cụt, (2) Bánh chưng mọc lơ lửng ngoài tay, (3) Bánh chưng style 3D/Photorealistic lạc quẻ giữa tranh vẽ tay. |
| **AC (Kết quả đúng)** | Hamburger biến mất, Bánh Chưng nằm trọn vặn trên tay. Phong cách hình vẽ khớp nét cũ. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.2 — Khớp Phong Cách Nghệ Thuật (Style Consistency)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 11, đoạn 2 — Gà Tây trên bàn tiệc |
| **Sách gốc (Input)** | Hình minh họa Turkey (Gà Tây nướng) style Watercolor. Text đổi thành "Gà luộc lá chanh". |
| **WA (Sai điển hình)** | Hệ thống sinh ra một con gà luộc, nhưng nét vẽ là Anime, Vector rực rỡ, hoặc tả thực khác hẳn phần nền xung quanh. |
| **AC (Kết quả đúng)** | Con gà luộc được sinh ra MƯỢT MÀ với đúng chất liệu màu nước (Watercolor), cùng độ bão hòa màu và độ loang với bàn tiệc. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.3 — Sinh Mới Bối Cảnh (Full Scene Generation)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 13, hình minh họa Rocky Mountains |
| **Sách gốc (Input)** | Hình nền núi đá Rocky xám gắt, tuyết phủ trắng. Text đổi thành "Đỉnh Fansipan". |
| **WA (Sai điển hình)** | Vẫn giữ nguyên khối núi Tây. Chỉ chèn chữ gượng gạo. |
| **AC (Kết quả đúng)** | AI phát hiện cảnh quan sai lệch, tự động tái tạo núi thành dạng ruộng bậc thang hoặc sương mù vùng cao Tây Bắc, thay đổi cả thảm thực vật sang nhiệt đới. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.4 — Tương tác Ánh sáng / Màu sắc (Lighting & Tone Match)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 7, hình minh họa Subway |
| **Sách gốc (Input)** | Cảnh ga tàu điện ngầm tối, ánh chớp đèn vàng leo lét. Text đổi thành "Bến Xe Khách". |
| **WA (Sai điển hình)** | Bến xe khách dán vào hình sáng trưng như ban ngày, mất đi độ sâu trường ảnh và hướng chiếu sáng của bản gốc. |
| **AC (Kết quả đúng)** | Vật thể Bến Xe Khách vẫn giữ được Tone màu mờ ảo, tối tăm, đổ bóng khớp với hệ thống đèn neon hắt ra từ góc ảnh. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.5 — Trích xuất & Cập nhật diện mạo nhân vật (Character Trait Adjustment)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 8, cậu bé Ironfist mặc len mùa đông |
| **Sách gốc (Input)** | Ironfist quàng khăn len, đội mũ len ở xứ lạnh. Phase 3 bản địa hoá sang xứ nóng mặc "áo cộc tay". |
| **WA (Sai điển hình)** | AI thay áo cộc tay nhưng không nhận diện được mặt khuôn mặt cũ của Ironfist, biến cậu ấy thành một đưa trẻ lạ hoắc. |
| **AC (Kết quả đúng)** | Giữ vững ID khuôn mặt của Ironfist (Trait Identification), chỉ thay thế phần quần áo trên người. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.6 — Triệt tiêu triệt để yếu tố Tôn giáo / Chính trị trên ảnh

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 19, hình minh họa bốt điện thoại London |
| **Sách gốc (Input)** | Bốt điện thoại đỏ dán cờ Anh Quốc. Text đổi thành cột điện/hộp thư VN. |
| **WA (Sai điển hình)** | AI đổi hình hộp thư VN nhưng trên thân hộp thư vẫn có một logo Vương Quốc Anh mờ mờ quên không tẩy gốc. |
| **AC (Kết quả đúng)** | Cờ cũ bị triệt tiêu 100%. Phần background trống trải sau nó được bù đắp (Inpainting out) bằng gạch tường đồng bộ. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.7 — Tái tạo chữ trên chất liệu (Text Rendering on Materials)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 12, Biển hiệu gỗ "BAKERY" |
| **Sách gốc (Input)** | Chữ BAKERY được khắc sâu vào thớ gỗ, đổ bóng vàng ánh kim. |
| **WA (Sai điển hình)** | Phase 4 quẹt một lớp nền xám phẳng đè lên ảnh, sau đó gõ một Text Box Arial "TIỆM BÁNH" vào. Không gắn với phối cảnh. |
| **AC (Kết quả đúng)** | Chữ "TIỆM BÁNH" uốn lượn theo vân gỗ, hiệu ứng khắc sâu (Emboss/Engrave), góc nghiêng 15 độ khớp góc phối cảnh gốc. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.8 — Chữ Vừa Bong Bóng Thoại (Bubble Fit)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 7, giữa trang — Speech Bubble khung viền đen |
| **Sách gốc (Input)** | Speech Bubble chứa `"Let's go!"` (3 từ). Tiếng Việt dịch: *"Chúng mình đi thôi nào!"* (5 từ) — dài gấp đôi. |
| **WA (Sai điển hình)** | Chữ Việt tràn ra ngoài viền bong bóng hoặc bị cắt xén mất chữ. |
| **AC (Kết quả đúng)** | Text Wrap tự động xuống dòng gọn gàng trong Bubble trắng, không lẹm viền, không đổi màu viền. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.9 — Tự Thiết Kế Lại Layout Khi Kẹt Cứng (Layout Engine / Auto-Summarize)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 18, Tiny Bubble `MEOW` |
| **Sách gốc (Input)** | Bong bóng thoại **rất nhỏ** (width ~3cm) không đủ chỗ cho chữ quá dài. |
| **WA (Sai điển hình)** | Chữ tràn nát nền PDF hoặc ép font < 5pt không thể đọc nổi. |
| **AC (Kết quả đúng)** | Phase 4 tự động kéo giãn bong bóng thoại đè lên nền trống, hoặc thu chữ về dạng "Meo!" an toàn. Giữ độ lớn đọc được rõ. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 4.10 — Xóa Chữ Nền Chuyên Nhẹ (Text Inpainting base)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3, chữ `IT WAS A BEAUTIFUL DAY` trên bầu trời |
| **Sách gốc (Input)** | Chữ to vắt ngang lớp mây trong hình. |
| **WA (Sai điển hình)** | AI bóp méo đám mây thành các vệt nhòe pixels (Artifacts) xung quanh dòng chữ bị tẩy. |
| **AC (Kết quả đúng)** | Inpainting lấp kín một cách trong trẻo, mây trôi tự nhiên như chưa từng có chữ ở đó. Nhét được thông điệp chữ Việt mới lên trên. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

## 🟣 PHASE 5 — TỔNG KIỂM TOÁN NGHIỆM THU (QA FINAL)

> Kiểm tra: Lưới lọc cuối cùng trước khi xuất bản. Chỉ hay đúng 3 hạng mục sinh tử: (1) Typo, (2) Logic Cánh Bướm xuyên sách, (3) Vi phạm Luật Cấm từ Brief.

---

### Test 5.1 — Rà Dấu Câu & Lỗi Typo (Grammar Check)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Toàn bộ sách (trang 3–22) |
| **Sách gốc (Input)** | Văn bản tiếng Anh gốc hoàn toàn bình thường |
| **Ví dụ lỗi (WA)** | File xuất ra có các lỗi: *"cô bé  bay đi"* (2 dấu cách), hoặc *"cô bé , nhảy lên"* (dấu phẩy lơi cách xa), hoặc *"cô bé đi dài.."* (dư dấu chấm) |
| **AC (Kết quả đúng)** | Hệ thống QA phát hiện lỗi dấu câu/khoảng trắng bất thường → Bắn tín hiệu **REJECT** → Yêu cầu Phase 2/3 chỉnh sửa và xuất lại. File cuối cùng không tồn tại bất kỳ lỗi định dạng nào. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 5.2 — Sốc Cánh Bướm Xuyên Sách (Butterfly Logic Collision)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 3 (`"the ancient Kingdom"`) + Trang 16 (`"find the Kingdom"`) + Trang 21 (`"Best pastries in the Kingdom"`) + Trang 22 (`"The Kingdom stretched before him"`) |
| **Ví dụ lỗi (WA)** | Trang 3 dịch *"Vương quốc"*, Trang 21 dịch *"Đất nước"*, Trang 22 dịch *"Hoàng cung"* — Mỗi trang gọi khác nhau |
| **AC (Kết quả đúng)** | QA quét toàn sách, phát hiện bất nhất → **REJECT** → chỉ rõ trang xung đột → Phase 3 đồng bộ lại. File cuối: 1 cách dịch duy nhất. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

### Test 5.3 — Lưới Lọc Luật Cấm (Global Constraints Audit)

| Mục | Nội dung |
|---|---|
| **Trang PDF** | Trang 6, đoạn 1: `"He brutally killed the beast with his sword, slashing through the darkness"` |
| **Constraint** | `never_change_rules: ["Cấm mọi từ ngữ bạo lực"]` |
| **Ví dụ lỗi (WA)** | Bản dịch cuối vẫn chứa: *"Cậu ta tàn nhẫn giết chết con quái vật bằng kiếm, chém xuyên bóng tối"* — Phase 2/3 để lọt từ bạo lực |
| **AC (Kết quả đúng)** | QA phát hiện vi phạm → **REJECT** → chỉ rõ trang 6 + nội dung vi phạm → Phase 2 sửa lại. File cuối sạch 100%. |

| AC | WA | Note |
|:---:|:---:|---|
| [ ] | [ ] | |

---

## 📊 BẢNG TỔNG KẾT

| Phase | Tổng Test | AC | WA | Tỉ lệ Pass |
|:---:|:---:|:---:|:---:|:---:|
| Phase 1 — Brief Parsing | 4 | ___ | ___ | ___% |
| Phase 2 — Translation | 10 | ___ | ___ | ___% |
| Phase 3 — Localization | 10 | ___ | ___ | ___% |
| Phase 4 — Visual Reconstruction | 10 | ___ | ___ | ___% |
| Phase 5 — QA Final | 3 | ___ | ___ | ___% |
| **TỔNG CỘNG** | **37** | ___ | ___ | **___% ** |

> **Tiêu chuẩn xuất bản:** Tỉ lệ Pass phải đạt **x%** (x/31 AC) mới được phép Merge code hoặc Demo trước ban giám khảo.

---

*Lưu ý: Tất cả số trang đã được gán chính xác theo file `test_cases/TestingBook.pdf` (22 trang). Mọi PR hoặc Demo bắt buộc phải AC toàn bộ Test Cases trên.*
