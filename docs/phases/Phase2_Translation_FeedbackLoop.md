# OmniLocal — Phase 2: Constrained Translation & Feedback Loop

> **Dự án:** OmniLocal — Hệ thống nội địa hóa sách thiếu nhi đa tác tử  
> **Đội ngũ:** APCS 24A01 · GDGoC 2026  
> **Bản quyền:** © 2026 Team APCS 24A01 — GDGoC 2026. All rights reserved.  
> **Phiên bản:** v1.0 · Tháng 4/2026

---

## 1. Tổng quan Phase

**Mục tiêu:** Nhận toàn bộ text từ Phase 1, thực hiện dịch thuật **tuân thủ global constraints**, và vận hành cơ chế tự đánh giá–phản biện giữa hai tác tử AI (Translator ↔ Reviser) để đảm bảo chất lượng dịch thuật.

**Đầu vào (Inputs):**

| # | Tên | Nguồn | Mô tả |
|---|-----|-------|-------|
| 1 | Standardized Pack | Phase 1 API | JSON chứa `text_blocks` kèm tọa độ bbox, editability tags |
| 2 | `global_metadata.json` | Phase 1 | Các ràng buộc toàn cục (tên riêng, phong cách dịch, giới hạn kỹ thuật) |

**Đầu ra (Outputs):**

| # | Tên | Mô tả | Định dạng |
|---|-----|-------|-----------|
| 1 | Verified Text Pack | Bản dịch tiếng Việt đã thẩm định, kèm tọa độ bbox gốc | JSON via API |
| 2 | Warning Tags | Danh sách chunk chưa đạt chất lượng sau 3 lần retry | JSON |

---

## 2. Phân rã nhiệm vụ (Task Breakdown)

### Task #p2.1 — Nhận dữ liệu & Phân mảnh (Semantic Chunking)

**Vấn đề:**  
Nếu ném toàn bộ sách vào LLM cùng lúc sẽ gây **tràn Context Window** và dẫn đến **ảo giác (hallucination)**.

**Nhiệm vụ:**

1. Lấy toàn bộ mảng `Text_Blocks` từ Standardized Pack (Phase 1 API).
2. Nhóm các block thành từng **Chunk** khoảng **10–15 trang/lần gọi API**.
3. **Bắt buộc** giữ nguyên mapping tọa độ `[x0, y0, x1, y1]` gắn với từng câu chữ — dữ liệu này sẽ cần cho Phase 4.

**Đầu ra:** Các mảng `Text_Blocks` đã được chia nhỏ, sẵn sàng để dịch.

---

### Task #p2.2 — Chuyển ngữ có Ràng buộc (Translator Agent)

**Vấn đề:** Dịch sát nghĩa gốc nhưng **PHẢI** tuân thủ mọi luật trong `global_metadata.json` (ví dụ: cấm dịch tên nhân vật).

**Nhiệm vụ:**

Gọi API LLM (**Gemini 2.5 Pro**) với cấu hình:

- **System Prompt:** Bắt buộc nạp toàn bộ `global_metadata.json` vào System Prompt.
- **Chỉ thị cứng (Directive):**

```
Bạn là dịch giả chuyên nghiệp. Dưới đây là nội dung cần dịch từ tiếng Anh sang 
tiếng Việt. Hãy dịch sát nghĩa gốc nhất có thể.
TUYỆT ĐỐI tuân thủ các luật sau:
- Không dịch các tên riêng: {protected_names}
- Không thay đổi màu sắc mô tả nhân vật
- Sử dụng ngôn ngữ phù hợp cho {style_register}
[... các luật khác từ global_metadata.json ...]
```

**Đầu ra:** Bản dịch thô (**Draft Target Text**).

---

### Task #p2.3 — Giám khảo AI (Reviser Agent)

**Vấn đề:** Cần đánh giá bản dịch ở Task #p2.2 **tự động** và sinh feedback nếu chất lượng không đạt.

**Nhiệm vụ:**

Gọi LLM (cùng model, **prompt khác**). Nạp đầu vào:
- Câu tiếng Anh gốc (Source Text)
- Bản dịch thô (Draft Target Text)
- `global_metadata.json`

**Prompt Giám khảo:**

```
Đánh giá bản dịch này có sát nghĩa gốc và tuân thủ luật dự án không.
Chấm điểm từ 1 đến 10.
Chỉ trả về JSON gồm:
{ "score": <số điểm>, "reason": "<giải thích ngắn gọn nếu điểm < 8>" }
```

**Đầu ra:** JSON chứa điểm số và lý do lỗi.

```json
{ "score": 6, "reason": "Dịch sai tên nhân vật 'Elsa' thành 'Công chúa Băng'" }
```

---

### Task #p2.4 — Vòng lặp đàm phán (Feedback Loop Engine)

**Vấn đề:** Ép hai Tác tử làm việc với nhau cho đến khi ra kết quả tốt, nhưng tránh treo hệ thống.

**Nhiệm vụ:**

Viết vòng lặp `while` trong Python:

```
┌──────────────────────────────────────────────┐
│                                              │
│  Translator Agent (Task #p2.2)               │
│      │                                       │
│      ▼                                       │
│  Reviser Agent (Task #p2.3)                  │
│      │                                       │
│      ▼                                       │
│  score ≥ 8?  ──── YES ──▶  PASS ──▶ Lưu kết quả    │
│      │                                       │
│      NO                                      │
│      │                                       │
│  retry < 3? ──── YES ──▶  Gửi `reason` về   │
│      │                    Translator Agent    │
│      │                    (lặp lại)           │
│      NO                                      │
│      │                                       │
│      ▼                                       │
│  CIRCUIT BREAK: Giữ bản dịch vòng cuối       │
│  + Dán tag WARNING để con người sửa sau      │
│                                              │
└──────────────────────────────────────────────┘
```

**Điều kiện routing:**

| Điều kiện | Hành động |
|-----------|----------|
| `score >= 8` | **PASS** — Lưu kết quả thành `Verified Target Text` |
| `score < 8` AND `retry < 3` | **RETRY** — Gửi `reason` về Translator Agent để gen lại |
| `score < 8` AND `retry >= 3` | **CIRCUIT BREAK** — Giữ bản dịch vòng cuối, dán tag `[WARNING]` |

**Tham số Circuit Breaker:** `max_retries = 3`

**Đầu ra:** JSON **`Verified Text Pack`** chứa:
- Bản dịch tiếng Việt đã thẩm định
- Tọa độ `[x0, y0, x1, y1]` gốc cho từng block
- Warning tags (nếu có)

Sẵn sàng chuyển sang Phase 3.

---

### Task #p2.5 — Đóng gói và Mở cổng giao tiếp (API Handoff)

**Vấn đề:** Các Tác tử ở Phase 3, 4, 5 cần đường dẫn chuẩn để lấy kết quả dịch thuật.

**Nhiệm vụ:**

Dùng **FastAPI** bọc `Verified Text Pack` thành Endpoint:

```
GET /api/v1/verified-text/{chunk_id}
GET /api/v1/verified-text/warnings
```

**Đầu ra:** Cổng API sẵn sàng trả dữ liệu cho phần còn lại của hệ thống.

---

## 3. Tech Stack

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.10+ |
| LLM | Gemini 2.5 Pro (API) |
| API framework | FastAPI + Uvicorn |

---

## 4. Dependency Map

```
Standardized Pack (Phase 1)
        │
        ▼
Task #p2.1 (Semantic Chunking)
        │
        ▼
Task #p2.2 (Translator Agent) ◀──┐
        │                         │  Feedback: reason
        ▼                         │
Task #p2.3 (Reviser Agent)       │
        │                         │
        ▼                         │
Task #p2.4 (Feedback Loop) ──────┘
        │
        ▼
Task #p2.5 (API Handoff)
        │
        ▼
    Phase 3
```

---

## 5. Lưu ý quan trọng cho Partners

1. **Giữ nguyên tọa độ bbox** khi trả kết quả — Phase 4 phụ thuộc vào mapping text ↔ vị trí trên trang.
2. **Circuit Breaker** là thiết yếu — không được xóa cơ chế `max_retries` để tránh vòng lặp vô hạn.
3. **Warning tags** phải được lưu riêng để Phase 5 (QA) và con người có thể review lại.
