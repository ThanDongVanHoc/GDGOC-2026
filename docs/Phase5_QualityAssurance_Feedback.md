# OmniLocal — Phase 5: Quality Assurance & Cross-Phase Feedback

> **Dự án:** OmniLocal — Hệ thống nội địa hóa sách thiếu nhi đa tác tử  
> **Đội ngũ:** APCS 24A01 · GDGoC 2026  
> **Bản quyền:** © 2026 Team APCS 24A01 — GDGoC 2026. All rights reserved.  
> **Phiên bản:** v1.0 · Tháng 4/2026

---

## 1. Tổng quan Phase

**Mục tiêu:** Rà soát toàn bộ tệp dữ liệu cuối cùng (Final State) để đảm bảo:

1. **Không có lỗi văn bản** (typo, ngắt câu thiếu tự nhiên)
2. **Không gãy logic hệ thống** (Butterfly Effect)
3. **Không vi phạm** các quy tắc bản quyền đã thiết lập ở Phase 1

**Đặc điểm quan trọng:** Phase 5 có khả năng **gửi ngược (feedback loop)** về Phase 3 hoặc Phase 4 nếu phát hiện lỗi — tạo thành vòng lặp xuyên Phase.

**Đầu vào (Inputs):**

| # | Tên | Nguồn | Mô tả |
|---|-----|-------|-------|
| 1 | PDF hoàn chỉnh | Phase 4 | File PDF truyện tranh tiếng Việt đã composit |
| 2 | `global_metadata.json` | Phase 1 | Ràng buộc toàn cục ban đầu |
| 3 | Localization Log | Phase 3 | Danh sách mọi thay đổi nội địa hóa |

**Đầu ra (Outputs):**

| # | Tên | Mô tả |
|---|-----|-------|
| 1 | QA Status | `PASS` hoặc `FAIL` (kèm loại lỗi) |
| 2 | Print-Ready PDF | Nếu PASS — file PDF cuối cùng đạt chuẩn |
| 3 | Feedback Signals | Nếu FAIL — chỉ thị gửi ngược về Phase tương ứng |

---

## 2. Phân rã nhiệm vụ (Task Breakdown)

### Task #p5.1 — Dò Typo & Cân bằng đoạn (Textual Integrity)

**Vấn đề:**  
Sau các vòng lặp tóm tắt (Summarization) ở Phase 4, văn bản có thể bị:
- Sót **lỗi chính tả** (typo)
- **Ngắt câu thiếu tự nhiên**
- Mất **kết nối ngữ nghĩa** giữa các đoạn

**Nhiệm vụ:**

- **QA Agent** quét toàn bộ văn bản trong PDF cuối.
- Sử dụng **từ điển tiếng Việt** để phát hiện lỗi typo.
- Kiểm tra tính tự nhiên của văn phong, đặc biệt ở các đoạn bị tóm tắt (Summarization) trong Phase 4.

**Feedback Loop:**

| Kết quả | Hành động |
|---------|----------|
| Không có lỗi ✅ | Chuyển sang Task #p5.2 |
| Phát hiện typo ❌ | Gửi ngược về **Localization Agent (Phase 3, Task #p3.2)** để sửa |

---

### Task #p5.2 — Kiểm soát Hiệu ứng Cánh bướm (Butterfly Effect Guardrail)

**Vấn đề:**  
Các thay đổi nội địa hóa (VD: đổi "xe buýt" thành "xe ngựa") có thể mâu thuẫn với các sự kiện ở các trang sau. Đây là lần kiểm tra cuối cùng — **tổng thể toàn bộ cuốn sách**.

**Nhiệm vụ:**

- Tác tử **so khớp** danh sách thực thể đã thay đổi (**Localization Log** từ Phase 3) với nội dung toàn bộ tệp tài liệu cuối.
- Phát hiện **xung đột logic** giữa các thay đổi và bối cảnh còn lại.

**Ví dụ xung đột:**
> Trang 5: Đổi "xe buýt" → "xe ngựa"  
> Trang 12: Vẫn còn đoạn "... đậu xe ở bến xe buýt"  
> → **CONFLICT** — logic không nhất quán

**Feedback Loop:**

| Kết quả | Hành động |
|---------|----------|
| Không có xung đột ✅ | Chuyển sang Task #p5.3 |
| Phát hiện gãy logic ❌ | Gửi ngược về **Butterfly Validator (Phase 3, Task #p3.3)** để "họp" lại phương án thay đổi |

---

### Task #p5.3 — Đối soát Ràng buộc Toàn cục (Global Constraints Check)

**Vấn đề:**  
Đảm bảo các quy tắc "khóa" từ Phase 1 (giữ nguyên tên riêng, giữ nguyên màu sắc vật thể đặc trưng) **không bị** các Agent cấp dưới tự ý thay đổi trong suốt pipeline.

**Nhiệm vụ:**

Chạy **Validation Script** đối soát giữa:
- Kết quả cuối cùng (PDF hoàn chỉnh)
- Bản `global_metadata.json` ban đầu (Phase 1)

**Các điểm kiểm tra:**

| # | Kiểm tra | Nguồn so sánh |
|---|----------|----------------|
| 1 | Tên riêng có bị dịch/thay đổi không? | `protected_names` trong metadata |
| 2 | Màu sắc nhân vật có bị thay đổi không? | `lock_character_color` trong metadata |
| 3 | Background có bị edit khi không được phép? | `allow_bg_edit` trong metadata |

**Feedback Loop:**

| Kết quả | Hành động |
|---------|----------|
| Tất cả OK ✅ | **PASS** — Xuất PDF cuối cùng |
| Vi phạm màu sắc ❌ | Gửi ngược về **Vision Agent (Phase 4, Task #p4.2)** — sai hình ảnh |
| Vi phạm tên riêng ❌ | Gửi ngược về **Localization Agent (Phase 3, Task #p3.2)** — sai text |

---

## 3. Sơ đồ Feedback Loop xuyên Phase

```
                    ┌────────────────────────────────────────────┐
                    │              PHASE 5: QA                   │
                    │                                            │
                    │  Task #p5.1 ──▶ Task #p5.2 ──▶ Task #p5.3 │
                    │      │              │              │        │
                    └──────┼──────────────┼──────────────┼────────┘
                           │              │              │
              ┌────────────┘              │              │
              ▼                           ▼              │
   Phase 3: Task #p3.2          Phase 3: Task #p3.3     │
   (Localization Agent)         (Butterfly Validator)    │
   - Sửa typo                  - Họp lại phương án      │
   - Sửa tên riêng                                      │
                                                         ▼
                                              Phase 4: Task #p4.2
                                              (Vision Agent)
                                              - Sửa màu sắc
                                              - Sửa hình ảnh
```

---

## 4. Bảng tổng hợp QA Status

| QA Status | Mô tả | Hành động tiếp theo |
|-----------|-------|---------------------|
| `pass` | Tất cả kiểm tra đều OK | Xuất **Print-Ready PDF** ✅ |
| `fail_typo` | Phát hiện lỗi chính tả/ngắt câu | → Phase 3: Localization Agent |
| `fail_butterfly` | Phát hiện gãy logic liên chương | → Phase 3: Butterfly Validator |
| `fail_constraint_visual` | Vi phạm ràng buộc hình ảnh | → Phase 4: Vision Agent |
| `fail_constraint_text` | Vi phạm ràng buộc text | → Phase 3: Localization Agent |

---

## 5. Dependency Map toàn hệ thống (liên Phase)

```
Phase 1 ──▶ Phase 2 ──▶ Phase 3 ──▶ Phase 4 ──▶ Phase 5
                              ▲          ▲          │
                              │          │          │
                              └──────────┴──────────┘
                                  Feedback Loops
                              (khi QA phát hiện lỗi)
```

---

## 6. Lưu ý quan trọng cho Partners

1. **Phase 5 không phải bước cuối cùng đơn giản** — nó là **bộ điều khiển phản hồi** cho toàn bộ pipeline. Mọi lỗi phát hiện ở đây sẽ kích hoạt sửa chữa ở Phase trước.

2. **Localization Log** (từ Phase 3) là **tài liệu sống** — Phase 5 phụ thuộc hoàn toàn vào tính đầy đủ và chính xác của log này.

3. **Cần đặt giới hạn iteration** cho feedback loop xuyên Phase để tránh vòng lặp vô hạn (khuyến nghị: tối đa 2 vòng toàn pipeline).

4. Sau khi Phase 5 `PASS`, file PDF cuối cùng phải đáp ứng đầy đủ **5 tiêu chuẩn Publishing Compliance** đã hardcode ở Phase 4:
   - CMYK color space
   - 300 DPI minimum
   - 5mm safe margin
   - K-Black 100% text
   - Font embedding

---

_Hết Phase 5 — Kết thúc pipeline OmniLocal._
