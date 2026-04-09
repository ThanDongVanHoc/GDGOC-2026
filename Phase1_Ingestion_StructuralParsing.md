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
| 2 | Yêu cầu dự án (Project Brief) | Cặp ngôn ngữ, phong cách dịch, ràng buộc bản quyền — thường ở dạng email, Word, hoặc Excel | DOCX / XLSX / Email |

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

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `source_language` | `string` | Ngôn ngữ gốc (EN) |
| `target_language` | `string` | Ngôn ngữ đích (VI) |
| `style_register` | `string` | Phong cách dịch ("trẻ em dưới 10 tuổi") |
| `allow_bg_edit` | `boolean` | Cho phép chỉnh sửa background hay không |
| `lock_character_color` | `boolean` | Khóa màu sắc nhân vật |
| `protected_names` | `string[]` | Danh sách tên riêng không được dịch |
| `max_drift_ratio` | `float` | Ngưỡng từ chối tại Phase 2 |

- **Đầu ra:** `global_metadata.json`

---

### Task #p1.2 — Bóc tách tọa độ không gian (Structural Parsing)

**Vấn đề:** Cần biết chữ và hình nằm ở đâu trên trang vật lý.

**Nhiệm vụ:**

Dùng thư viện **PyMuPDF** (`fitz`) đọc file PDF đầu vào:

1. Quét từng trang, sử dụng `page.get_text("dict")` để trích xuất:
   - Mảng **`Text_Blocks`**: nội dung chữ kèm tọa độ `[x0, y0, x1, y1]`
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
Kết hợp `global_metadata.json` (Task #p1.1) và JSON tọa độ (Task #p1.2), gán **3 tag** cho từng block:

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
