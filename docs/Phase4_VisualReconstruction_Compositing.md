# OmniLocal — Phase 4: Visual Reconstruction & Print-Ready Compositing

> **Dự án:** OmniLocal — Hệ thống nội địa hóa sách thiếu nhi đa tác tử  
> **Đội ngũ:** APCS 24A01 · GDGoC 2026  
> **Bản quyền:** © 2026 Team APCS 24A01 — GDGoC 2026. All rights reserved.  
> **Phiên bản:** v1.0 · Tháng 4/2026

---

## 1. Tổng quan Phase

**Mục tiêu:**

1. **Tái tạo bối cảnh** nguyên bản nghệ thuật nhất (Inpainting + ControlNet).
2. **Dùng Toán học** để tính toán chính xác khung chữ, sau đó đặt tiếng Việt vào ảnh bằng ReportLab (chữ vector) để đảm bảo tiêu chuẩn in ấn.
3. **Xuất file PDF** đáp ứng 100% tiêu chuẩn in ấn công nghiệp (Publishing Compliances).

**Đầu vào (Inputs):**

| # | Tên | Nguồn | Mô tả |
|---|-----|-------|-------|
| 1 | Context-safe Localized Text Pack | Phase 3 API | Bản text đã nội địa hóa, an toàn logic, kèm bbox |
| 2 | File PDF gốc | Phase 1 | Ảnh gốc của từng trang sách |

**Đầu ra (Outputs):**

| # | Tên | Mô tả | Định dạng |
|---|-----|-------|-----------|
| 1 | File PDF hoàn chỉnh | Truyện tranh tiếng Việt, đạt chuẩn in ấn công nghiệp | PDF (CMYK, 300 DPI) |

**Kiến trúc:** Phase 4 được chia thành **3 Track song song**, hợp nhất ở cuối:

```
                    ┌─── Track A: Scene Reconstruction ───┐
                    │                                      │
Phase 3 Output ────┤                                      ├──▶ Track C: Compositing ──▶ PDF
                    │                                      │
                    └─── Track B: Math-Guided Text ───────┘
```

---

## 2. Pipeline tổng thể (Gợi ý)

| Bước | Nội dung | Công nghệ |
|------|----------|-----------|
| **Nhận diện** (Task #p4.1) | VLM nhận diện tọa độ Vật thể A (Lò sưởi) và các Khung thoại | Gemini Vision / VLM |
| **Tiền xử lý** (Task #p4.2 – OpenCV) | Dùng OpenCV "tẩy mực" khung thoại — inpaint cục bộ để có nền sạch, giữ viền và texture giấy | OpenCV |
| **Tạo Mask** (Task #p4.2 – Dev Logic) | Tạo ảnh đen hoàn toàn → vẽ vùng Vật thể A = **Trắng** → giữ Khung thoại = **Đen** | OpenCV |
| **AI Inpainting** (Task #p4.2 – Vision API) | AI thấy vùng trắng (Lò sưởi) → vẽ thành B (Bếp củi). Vùng đen → giữ nguyên | Stable Diffusion + ControlNet |
| **Dàn trang** (Task #p4.3 → #p4.5) | Toán tính tọa độ → ReportLab bắn chữ Vector lên ảnh hoàn thiện | Knuth-Plass + ReportLab |

---

## 3. Track A — Tái tạo bối cảnh (Scene Reconstruction)

### Task #p4.1 — Nhận diện & Khoanh vùng (Context Masking)

**Vấn đề:** AI cần biết vùng nào để vẽ lại vật thể, vùng nào để xóa chữ.

**Nhiệm vụ:**

Dùng OpenCV lấy tọa độ, sinh ra **Mask (Mặt nạ)** bao trọn:
- Các thực thể bị nội địa hóa (VD: Lò sưởi)  
- Các text bubble (Khung thoại)

**Phương pháp nhận diện vật thể trong ảnh:**
- **Full scope:** Grounding DINO + SAM (Segment Anything Model)
- **Down scope (MVP):** Dùng VLM (Vision Language Model) để nhận diện

**Đầu ra:** Mask per-page.

---

### Task #p4.2 — Tác tử Tái tạo Bối cảnh (Background & Art Agent)

**Vấn đề:** Phải ưu tiên **giữ nguyên Art-style** của tác giả gốc.

**Nhiệm vụ:**

1. Chạy **Inpainting + ControlNet** (Canny/Depth) để bảo toàn cấu trúc nét vẽ xung quanh.
2. AI thực hiện: Thay đổi vật thể nội địa hóa theo mô tả `A → B`.

**Quy trình tạo Mask cho Inpainting:**

| Bước | Mô tả |
|------|-------|
| 1 | Tạo ảnh **đen hoàn toàn** (kích thước = trang sách) |
| 2 | Vẽ vùng Vật thể A (cần thay) = **Màu Trắng** |
| 3 | Vùng Khung thoại (đã tẩy mực ở bước tiền xử lý) = giữ **Màu Đen** |
| 4 | Đưa ảnh gốc + Mask vào AI Inpainting |

**Kết quả:** AI thấy vùng trắng → vẽ lại. AI thấy vùng đen → giữ nguyên.

**Đầu ra Track A:** Tấm ảnh có bối cảnh hoàn hảo, trống trơn không còn chữ tiếng Anh.

---

## 4. Track B — Toán học Định hướng & AI Vẽ chữ (Math-Guided Rendering)

### Task #p4.3 — Engine Toán học Tính toán Layout (Mathematical Layout Engine)

**Vấn đề:**  
AI Vision rất **kém** trong việc tự canh lề. Nếu chỉ ném text cho AI bảo "vẽ đi", nó sẽ vẽ tràn ra ngoài hoặc chữ quá bé.

**Nhiệm vụ:**

Dùng **thuật toán Knuth-Plass** (Dynamic Programming) kết hợp **Hình học tính toán** để giả lập việc nhồi đoạn tiếng Việt vào Bounding Box gốc.

**Mục tiêu:** Không phải xuất ra chữ, mà xuất ra **Blueprint** (Bản thiết kế):

| Thông số | Mô tả |
|----------|-------|
| Tọa độ từng dòng | `[x, y]` chính xác trên trang |
| Font Size lý tưởng | Kích thước font tối ưu để vừa khung |
| Overflow Ratio | Tỷ lệ tràn (%) nếu không nhét vừa |

**Logic phân nhánh:**

| Kết quả | Hành động |
|---------|----------|
| `FIT` ✅ | Gửi Blueprint sang Task #p4.5 (Compositing) |
| `OVERFLOW` ❌ ratio: X% | Đẩy cờ `[OVERFLOW, Ratio: X%]` sang Task #p4.4 |

---

### Task #p4.4 — Tác tử Tóm tắt Định lượng (Anti-Overflow LLM Agent)

**Vấn đề:** Tránh việc AI tóm tắt mò mẫm — lúc thiếu, lúc thừa.

**Nhiệm vụ:**

1. Bắt sự kiện `OVERFLOW` từ Task #p4.3.
2. Nạp **con số tính toán** chính xác vào Prompt:

```
Đoạn văn này quá dài. Hãy tóm tắt lại, giảm CHÍNH XÁC {overflow_ratio}% 
độ dài nhưng phải giữ nguyên ý nghĩa cốt lõi và không làm mất các từ khóa 
thực thể.
```

3. Đẩy kết quả về lại Task #p4.3 để chạy lại Knuth-Plass.
4. **Circuit Breaker:** `max_retries = 2`

**Đầu ra Track B:** Text đã dàn đều tăm tắp, font size chuẩn chỉnh, khớp 100% diện tích khung hình.

---

## 5. Track C — Hợp nhất & Tuân thủ Tiêu chuẩn In ấn (Compositing)

### Task #p4.5 — Ráp khuôn & Thực thi Publishing Compliances

**Vấn đề:**  
Sản phẩm trên màn hình đẹp nhưng khi mang ra nhà in công nghiệp bị xỉn màu, vỡ hạt, hoặc lỗi font chữ. **Bắt buộc phải áp dụng luật xuất bản.**

**Nhiệm vụ:**  
Lấy **Ảnh** (Track A) và **Chữ** (Track B) ráp lại thành file PDF. Hardcode các ràng buộc sau:

### 5.1 Hệ màu CMYK (RGB → CMYK)

| | Mô tả |
|---|---|
| **Insight** | Mọi LLM/GenAI (Stable Diffusion, Midjourney) đều sinh ảnh **RGB**. Nhưng máy in công nghiệp chỉ chạy **CMYK**. Nếu để RGB mà in → màu xỉn, tối, sai lệch. |
| **Nhiệm vụ** | Convert ảnh inpaint từ RGB → CMYK bằng `Pillow` (dùng ICC profile: **U.S. Web Coated (SWOP) v2**) |

### 5.2 Mật độ ảnh 300 DPI

| | Mô tả |
|---|---|
| **Insight** | AI sinh ảnh thường 72/96 DPI (chuẩn web). In lên giấy truyện tranh sẽ **vỡ hạt (pixelated)**. |
| **Nhiệm vụ** | Thiết lập tham số giữ nguyên/ép **tối thiểu 300 DPI** khi trích xuất (Phase 1) và chèn lại (Phase 4) |

### 5.3 Vùng an toàn (Safe Margin)

| | Mô tả |
|---|---|
| **Insight** | Lưỡi dao cắt xén sách có thể xê dịch 2–3mm. Nếu text quá sát mép → bị cắt mất. |
| **Nhiệm vụ** | Thuật toán tính bbox (Task #p4.3) phải set **padding ảo 5mm** từ mép trang vật lý. Nếu chữ chạm vạch 5mm → coi như **OVERFLOW** → kích hoạt Anti-Overflow Agent |

### 5.4 K-Black 100% (Đen Pure)

| | Mô tả |
|---|---|
| **Insight** | Chữ đen phải in bằng 100% mực K (Key), **KHÔNG** dùng Rich Black (pha C+M+Y+K). Rich Black gây nhòe, viền màu (Registration error). |
| **Nhiệm vụ** | ReportLab set màu text = `CMYKColor(0, 0, 0, 1)` |

### 5.5 Font Embedding

| | Mô tả |
|---|---|
| **Insight** | Nếu không embed font tiếng Việt, nhà in sẽ thay bằng font lỗi (ô vuông). |
| **Nhiệm vụ** | Bắt buộc embed file `.ttf/.otf` tiếng Việt vào lõi PDF bằng ReportLab |

**Đầu ra cuối cùng:** File PDF truyện tranh tiếng Việt hoàn chỉnh, đạt chuẩn in ấn công nghiệp.

---

## 6. Bảng tổng hợp Publishing Compliance

| # | Quy tắc | Giá trị bắt buộc | Thư viện |
|---|---------|-------------------|----------|
| 1 | Hệ màu | RGB → CMYK (ICC: U.S. Web Coated SWOP v2) | `Pillow` |
| 2 | Mật độ ảnh | ≥ 300 DPI | `Pillow` / `PyMuPDF` |
| 3 | Vùng an toàn | Padding 5mm từ mép giấy | Math Layout Engine |
| 4 | Màu chữ | `CMYKColor(0, 0, 0, 1)` — K-Black 100% | `ReportLab` |
| 5 | Font | Embed `.ttf/.otf` tiếng Việt vào PDF | `ReportLab` |

---

## 7. Tech Stack

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.10+ |
| Xử lý đồ họa (Pixel) | `OpenCV-Python` (sinh Mask), `Pillow` (convert CMYK, DPI) |
| AI Image (API) | `HuggingFace API` / Replicate / Vertex — Stable Diffusion Inpainting + ControlNet |
| Toán học & Dàn trang | Thuật toán Knuth-Plass (DP tự viết) + `ImageFont` (đo Font Metrics) |
| Xử lý PDF & Nhúng Font | `ReportLab` (vẽ chữ, set K-Black) hoặc `PyMuPDF` (`fitz`) |

---

## 8. Dependency Map

```
Phase 3 Output
        │
        ├──────────────────────────────┐
        ▼                              ▼
  ┌─── Track A ───┐            ┌─── Track B ───────────┐
  │                │            │                        │
  │ Task #p4.1     │            │ Task #p4.3             │
  │ Context Masking│            │ Math Layout Engine     │
  │       │        │            │       │                │
  │       ▼        │            │       ▼                │
  │ Task #p4.2     │            │  Overflow? ── YES ──▶ Task #p4.4 (Anti-Overflow)
  │ Inpainting     │            │       │                │       │
  │ + ControlNet   │            │      NO                │       │ retry ≤ 2
  │       │        │            │       │                │       │
  └───────┼────────┘            │       ▼                │       ▼
          │                     │  Blueprint Ready       │  Gửi lại Task #p4.3
          │                     └───────┼────────────────┘
          │                             │
          └─────────────┬───────────────┘
                        ▼
              Track C: Compositing (Task #p4.5)
              Publishing Compliances
                        │
                        ▼
                 Print-Ready PDF
```

> **Lưu ý:** Track A và Track B có thể chạy **song song** — chúng không phụ thuộc lẫn nhau.
