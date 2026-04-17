# OmniLocal — Phase 1: Ingestion & Structural Parsing

> **Dự án:** OmniLocal — Hệ thống nội địa hóa sách thiếu nhi đa tác tử  
> **Đội ngũ:** APCS 24A01 · GDGoC 2026  
> **Bản quyền:** © 2026 Team APCS 24A01 — GDGoC 2026. All rights reserved.  
> **Phiên bản:** v1.0 · Tháng 4/2026

---

## 1. Tổng quan Phase

**Mục tiêu:** Chuyển đổi file PDF gốc và yêu cầu dự án (Project Brief) lộn xộn của khách hàng thành một **API Endpoint** cung cấp bản đồ JSON chuẩn hóa (**Standardized Pack**), bao gồm toàn bộ constraints, content blocks và editability tags phục vụ cho các Phase sau.

**Đầu vào (Inputs):**

| # | Tên | Mô tả | Định dạng |
|---|-----|-------|-----------|
| 1 | Tài nguyên vật lý (Assets) | File PDF xuất bản hoặc file InDesign (IDML) kèm thư mục ảnh (Links) và Font chữ | PDF / IDML |
| 2 | Yêu cầu dự án (Project Brief) | Cặp ngôn ngữ, phong cách dịch, ràng buộc bản quyền — thường ở dạng email, Word, hoặc Excel | DOCX / XLSX / Email / txt|

**Đầu ra (Outputs):**

| # | Tên | Mô tả | Định dạng |
|---|-----|-------|-----------|
| 1 | `global_metadata.json` | Ràng buộc toàn cục (bản quyền + kỹ thuật) | JSON |
| 2 | Standardized Pack | Gộp metadata + layout + editability tags | JSON via API |
| 3 | API Endpoint | `GET /api/v1/task-graph/{page_id}` | REST API |
| 4 | Docker Image | `omnilocal-phase1` | Dockerfile |

---

## 2. Phân rã nhiệm vụ (Task Breakdown)

### Task #p1.1 — Định nghĩa ranh giới bản quyền (Global Metadata Setup)

**Vấn đề nghiệp vụ:**  
Khách hàng **không bao giờ** giao cho đội ngũ một file JSON hay bộ metadata có cấu trúc. Thay vào đó, đội nhận được:

- **Assets:** File PDF xuất bản hoặc cục file InDesign kèm thư mục ảnh và font. **Không có** metadata về bối cảnh văn hóa hay cốt truyện.
- **Brief:** File Word/Excel hoặc đoạn email dặn dò, chứa nội dung như:
  - Cặp ngôn ngữ: EN → VI
  - Phong cách dịch: *"Dùng từ ngữ cho trẻ em dưới 10 tuổi"*
  - Ràng buộc bản quyền (lộn xộn): *"Giữ nguyên tên nhân vật chính"*, *"Không được vẽ đè lên mặt nhân vật"*, *"Đừng đổi màu áo nhân vật"*

**Subtask 1 — Sample Analysis:**

- Đưa ra một sample chuẩn về dữ liệu yêu cầu dự án nhận được từ khách hàng.  
- Tự đánh giá những trường nào cần trích xuất.  
- **Đầu ra:** `P1_st1_Normalize_Sample_Analysis.md`

**Subtask 2 — Xây dựng Global Constraints:**

Dựa trên kết quả Subtask 1, xây dựng các tham số:
Ví dụ:

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `source_language` | `string` | Ngôn ngữ gốc (EN) |
| `target_language` | `string` | Ngôn ngữ đích (VI) |
| `style_register` | `string` | Phong cách dịch ("trẻ em dưới 10 tuổi") |
| `allow_bg_edit` | `boolean` | Cho phép chỉnh sửa background hay không |
| `lock_character_color` | `boolean` | Khóa màu sắc nhân vật |
| `protected_names` | `string[]` | Danh sách tên riêng không được dịch |

- **Đầu ra:** `global_metadata.json`

---

### Task #p1.2 — Bóc tách tọa độ không gian (Structural Parsing)

**Vấn đề:** Cần biết chữ và hình nằm ở đâu trên trang vật lý.

**Nhiệm vụ:**

Dùng thư viện **PyMuPDF** (`fitz`) đọc file PDF đầu vào:

1. Quét từng trang, sử dụng `page.get_text("dict")` để trích xuất:
   - Mảng **`Text_Blocks`**: nội dung chữ kèm tọa độ `[x0, y0, x1, y1]`+ Font+ Size+ Color+Flags.
   - Mảng **`Image_Blocks`**: tọa độ hình ảnh `[x0, y0, x1, y1]`

**Đầu ra:** JSON tọa độ layout của từng trang sách.

```json
{
  "page_id": 1,
  "width": 595.0,
  "height": 842.0,
  "text_blocks": [
    { "content": "Once upon a time...", "bbox": [72, 100, 523, 130] }
  ],
  "image_blocks": [
    { "bbox": [50, 200, 545, 600] }
  ]
}
```

---

### Task #p1.3 — Dán nhãn quyền can thiệp (Editability Tagging)

**Vấn đề:** Các Phase sau cần biết vùng nào được sửa, vùng nào cấm đụng vào để không vi phạm bản quyền.

**Nhiệm vụ:**  
Kết hợp `global_metadata.json` (Task #p1.1) và JSON tọa độ (Task #p1.2), Ví dụ gán **3 tag** cho từng block (này tôi chỉ ví dụ bạn được phép sáng tạo để cho nó chuẩn hơn):

| Tag | Ý nghĩa | Ví dụ |
|-----|---------|-------|
| `editable` | Toàn quyền sửa (text + hình) | Background không chứa nhân vật |
| `semi-editable` | Chỉ sửa text, không sửa hình | Text bubble chứa nhân vật |
| `non-editable` | Khóa cứng, cấm can thiệp | Mặt nhân vật, logo bản quyền |

**Đầu ra:** Mảng JSON đã được đánh tag phân quyền rõ ràng.

---

### Task #p1.4 — Đóng gói và Mở cổng giao tiếp (API Handoff)

**Vấn đề:** Các Tác tử ở Phase 2, 3, 4 cần một đường dẫn chuẩn để lấy Task Graph.

**Nhiệm vụ:**

1. Gộp dữ liệu từ Task #p1.1, #p1.2 và #p1.3 lại thành **Standardized Pack**.
2. Dùng **FastAPI** bọc khối dữ liệu này thành Endpoint:

```
GET /api/v1/task-graph/{page_id}
```

**Đầu ra:** Cổng API sẵn sàng trả dữ liệu JSON cho phần còn lại của hệ thống.

---

### Task #p1.5 — Đóng gói môi trường (Containerization)

**Nhiệm vụ:** Đóng gói code bằng Docker để các partners có thể dùng và nộp cho ban tổ chức.

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Hướng dẫn sử dụng:**

```bash
docker build -t omnilocal-phase1 .
docker run -p 8000:8000 omnilocal-phase1
```

---

## 3. Tech Stack

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.10+ |
| Schema validation | `Pydantic` |
| PDF parsing | `PyMuPDF` (`fitz`) — `page.get_text("dict")` |
| API framework | `FastAPI` + `Uvicorn` |
| Containerization | `Docker` |

---

## 4. Dependency Map

```
Task #p1.1 (Global Metadata) ──┐
                                ├──▶ Task #p1.3 (Editability Tagging)
Task #p1.2 (Structural Parsing)┘         │
                                          ▼
                                   Task #p1.4 (API Handoff)
                                          │
                                          ▼
                                   Task #p1.5 (Containerization)
```

> **Lưu ý:** Task #p1.1 và Task #p1.2 có thể thực hiện **song song** vì không phụ thuộc lẫn nhau.

## 5.Example Global Constraints (Ràng buộc Toàn cục)

### Nhóm 1: Legal Parameters (Ràng buộc Pháp lý cứng)

Dựa trên nền tảng Quyền Nhân thân (Moral Rights), đặc biệt là Quyền đứng tên (Right of Paternity) và Quyền bảo vệ sự toàn vẹn của tác phẩm (Right of Integrity).

| **Tham số** | **Kiểu dữ liệu** | **Mô tả & Ràng buộc Thực tế** |
| --- | --- | --- |
| `license_status` | `boolean` | Trạng thái cấp phép hợp pháp. Nếu `false`, mọi hành vi dịch thuật/bóc tách text đều bị chặn để tránh vi phạm phái sinh. |
| `author_attribution` | `string` | Cú pháp bắt buộc để ghi nhận danh tính tác giả (Right of Paternity) trên bìa và trang bản quyền. |
| `integrity_protection` | `boolean` | Khóa tuyệt đối việc cắt xén, xuyên tạc nội dung có thể gây phương hại đến danh dự tác giả (Right of Integrity). |
| `adaptation_rights` | `boolean` | Quyền chuyển thể. Thường là `false` (chỉ được dịch, không được phóng tác, đổi bối cảnh, hay transcreation). |

### Nhóm 2: Content Parameters (Kiểm soát Nội dung)

Bảo đảm tính trung thành tuyệt đối với nguyên tác theo yêu cầu của hợp đồng.

| **Tham số** | **Kiểu dữ liệu** | **Mô tả & Ràng buộc Thực tế** |
| --- | --- | --- |
| `translation_fidelity` | `enum` | `Strict` (không thêm bớt), `Explanatory` (cho phép thêm các chú thích cực nhỏ để làm rõ nghĩa nhưng không đổi văn bản). |
| `plot_alteration` | `boolean` | Thay đổi cốt truyện.|
| `cultural_localization` | `boolean` | Cho phép "Việt hóa" các yếu tố văn hóa (ví dụ: đổi Hamburger thành Bánh mì). Thường là `false` để bảo toàn IP. |

### Nhóm 3: IP / Brand Parameters (Bảo toàn Nhận diện Thương quyền)

Bảo vệ "Kinh thánh Nhân vật" (Character Bible) và ranh giới đồ họa.

| **Tham số** | **Kiểu dữ liệu** | **Mô tả & Ràng buộc Thực tế** |
| --- | --- | --- |
| `preserve_main_names` | `boolean` | Bắt buộc giữ nguyên (chỉ phiên âm) tên nhân vật chính để bảo vệ tài sản thương hiệu và hoạt động bán đồ chơi ăn theo (Merchandising), tương tự cách xử lý tên Harry Potter. |
| `no_retouching` | `boolean` | Cấm vẽ đè, tẩy xóa hình ảnh gốc. Nếu hệ thống OCR bóc text làm mất hình, không được tự ý cho họa sĩ vẽ lại (redraw) hậu cảnh. |
| `lock_character_color` | `boolean` | Khóa màu sắc nhân vật theo thông số tuyệt đối (ví dụ: in đúng mã CMYK hoặc Pantone được chỉ định). |
| `never_change_rules` | `string[]` | Danh sách các đặc điểm ngoại hình bất di bất dịch (ví dụ: nốt ruồi dưới mắt trái, cấu trúc viền mũ) không được phép chỉnh sửa. |

### Nhóm 4: Editorial Parameters (Kiểm duyệt Biên tập)

Ràng buộc về văn phong và luồng công việc phê duyệt (Approval workflow).

| **Tham số** | **Kiểu dữ liệu** | **Mô tả & Ràng buộc Thực tế** |
| --- | --- | --- |
| `target_age_tone` | `integer` | Định hướng văn phong theo độ tuổi (ví dụ: `< 10` để thiết lập "giọng điệu" phù hợp cho trẻ em). |
| `glossary_strict_mode` | `boolean` | Ép buộc sử dụng 100% Cẩm nang Văn phong (Style Guides) và Danh mục thuật ngữ (Glossary) do bản gốc cung cấp. |
| `sfx_handling` | `enum` | Cách xử lý từ tượng thanh đồ họa: `In_panel_subs` (để phụ đề mờ bên cạnh), `Footnotes` (xuống cước chú), hoặc giữ nguyên. |
| `satisfaction_clause` | `boolean` | Điều khoản "Hài lòng": Bên cấp phép gốc có quyền phủ quyết toàn bộ bản dịch nếu họ đánh giá văn phong không "hoàn chỉnh và thỏa đáng" trước khi in. |