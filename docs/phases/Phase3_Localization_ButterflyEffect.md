# OmniLocal — Phase 3: Cultural Localization & Butterfly Effect Validation

> **Dự án:** OmniLocal — Hệ thống nội địa hóa sách thiếu nhi đa tác tử  
> **Đội ngũ:** APCS 24A01 · GDGoC 2026  
> **Bản quyền:** © 2026 Team APCS 24A01 — GDGoC 2026. All rights reserved.  
> **Phiên bản:** v1.0 · Tháng 4/2026

---

## 1. Tổng quan Phase

**Mục tiêu:** Nội địa hóa các thực thể văn hóa phương Tây sang bản địa (VD: "Lò sưởi" → "Bếp củi") để phù hợp với độc giả mục tiêu, **ĐỒNG THỜI** đảm bảo tuyệt đối không phá vỡ logic cốt truyện liên chương (**Butterfly Effect**) thông qua thuật toán duyệt đồ thị.

**Đầu vào (Inputs):**

| # | Tên | Nguồn | Mô tả |
|---|-----|-------|-------|
| 1 | `Verified Text Pack` | Phase 2 API | JSON chứa bản dịch đã thẩm định, giữ nguyên tọa độ bbox |
| 2 | `global_metadata.json` | Phase 1 | Luật toàn cục (giới hạn nội địa hóa) |

**Đầu ra (Outputs):**

| # | Tên | Mô tả | Định dạng |
|---|-----|-------|-----------|
| 1 | Context-safe Localized Text Pack | Bản text đã nội địa hóa, an toàn logic | JSON via API |
| 2 | Entity Graph | Cấu trúc dữ liệu đồ thị thực thể | In-memory |
| 3 | Localization Log | Danh sách mọi thay đổi thực thể | JSON |

---

## 2. Phân rã nhiệm vụ (Task Breakdown)

### Task #p3.1 — Tiền xử lý & Lập bản đồ Thực thể (Global Entity Pre-computation)

**Vấn đề:**  
Để tránh Butterfly Effect ở Task #p3.3, cần biết các thực thể nằm ở đâu và liên kết với nhau thế nào. Phải thiết kế **data structure** đủ tốt để truy vấn butterfly **nhanh** (mili-giây).

**Nhiệm vụ:**

1. **Viết script quét toàn bộ `Verified Text Pack`**, nhận diện và trích xuất các thực thể chính (nhân vật, địa điểm, vật thể, sự kiện thời tiết, phương tiện, v.v.)
2. **Bài toán thiết kế:** Xây dựng **Cấu trúc dữ liệu đồ thị** (Graph Data Structure) lưu trữ trong RAM:

```python
entity_graph = {
    "Tuyết": {
        "type": "weather_entity",
        "pages": [1, 3, 5, 12],
        "related": ["Người Tuyết", "Mùa đông", "Lạnh"],
        "contexts": [
            {"page": 3, "sentence": "Bọn trẻ nặn Người Tuyết giữa trời tuyết trắng"}
        ]
    },
    "Người Tuyết": {
        "type": "character",
        "pages": [3, 4, 5],
        "related": ["Tuyết", "Cà rốt", "Mũ len"],
        "contexts": [...]
    },
    # ...
}
```

> **Khuyến nghị thiết kế:** Sử dụng **Adjacency List** cho đồ thị thực thể. Mỗi node chứa metadata về loại, danh sách trang xuất hiện, và danh sách quan hệ (edges).

**Đầu ra:** Cấu trúc dữ liệu toàn cục về thực thể, sẵn sàng cho truy vấn BFS/DFS.

---

### Task #p3.2 — Tác tử Nội địa hóa (Localization Agent)

**Vấn đề:** Thay từ phương Tây bằng từ bản địa phù hợp, đảm bảo tuân thủ `global_metadata.json`.

**Nhiệm vụ:**

- Quét `Verified Text Pack` để tìm các thực thể cần nội địa hóa.
- Sinh ra **Proposals** (đề xuất thay đổi):

```json
{
    "proposal_id": "prop_001",
    "original": "Lò sưởi",
    "proposed": "Bếp củi",
    "affected_pages": [2, 7, 15],
    "rationale": "Lò sưởi không phổ biến ở Việt Nam, thay bằng bếp củi cho quen thuộc"
}
```

- Đảm bảo đề xuất **tuân thủ** `global_metadata.json` (VD: nếu `lock_character_color = true` thì không đề xuất thay đổi màu sắc).

**Đầu ra:** Danh sách Proposals.

---

### Task #p3.3 — Thuật toán Thẩm định Butterfly Effect (Butterfly Effect Validator)

**Vấn đề:**  
Đánh giá xem đề xuất của Task #p3.2 có an toàn để áp dụng cho **toàn bộ cuốn sách** không. **Tốc độ phải tính bằng mili-giây.**

**Nhiệm vụ:**

- **Input:** Đề xuất đổi `A → B` (VD: Tuyết → Mưa) + Entity Graph từ Task #p3.1.
- **Bài toán:** Viết thuật toán xác định xem việc đổi `A` → `B` có gây xung đột logic với bất kỳ bối cảnh nào ở các trang/chương khác không.

**Thuật toán đề xuất — BFS/DFS trên Entity Graph:**

```python
def butterfly_validator(proposal, entity_graph):
    """
    BFS thuần algo — KHÔNG gọi LLM tại bước này.
    Yêu cầu: Time Complexity tối ưu nhất có thể.
    """
    entity = proposal["original"]   # VD: "Tuyết"
    proposed = proposal["proposed"]  # VD: "Mưa"
    
    visited = set()
    queue = [entity]
    conflicts = []
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        node = entity_graph[current]
        for related in node["related"]:
            if has_semantic_conflict(proposed, related, node["contexts"]):
                conflicts.append({
                    "entity": related,
                    "page": node["pages"],
                    "reason": f"Không đổi '{entity}' thành '{proposed}' "
                              f"vì trang {node['pages']} có '{related}'"
                })
            queue.append(related)
    
    if conflicts:
        return {"status": "REJECT", "conflicts": conflicts}
    else:
        return {"status": "ACCEPT"}
```

**Logic phân nhánh:**

| Kết quả | Hành động |
|---------|----------|
| `ACCEPT` ✅ | Áp dụng proposal, tiến sang Task #p3.4 |
| `REJECT` ❌ | Gửi ngược về Task #p3.2 — Localization Agent phải nghĩ từ khác hoặc giữ nguyên |

> **ADVICE quan trọng:** Nên **hybrid** giữa algorithm và LLM:
> - Dùng **LLM** để xây dựng các node và cạnh của đồ thị (Task #p3.1).
> - Khi có update thì chỉ **retrieval update** trên các thành phần liên thông (cục bộ).
> - Dùng **thuần algorithm (BFS/DFS)** để validate — không gọi LLM tại bước validate.

---

### Task #p3.4 — Cập nhật Trạng thái & Đóng gói API (Mutation & API Handoff)

**Vấn đề:** Áp dụng thay đổi đã được chấp nhận và giao tiếp với Phase 4.

**Nhiệm vụ:**

1. Áp dụng tất cả Proposals đã `ACCEPT` vào `Verified Text Pack` → tạo ra **Context-safe Localized Text Pack**.
2. Cập nhật Entity Graph nếu cần (incremental update).
3. Lưu **Localization Log** — danh sách mọi thay đổi đã thực hiện (phục vụ Phase 5 QA).
4. Dùng **FastAPI** bọc lại thành Endpoint:

```
POST /api/v1/localize/page/{page_id}
GET  /api/v1/localized-text/{page_id}
GET  /api/v1/localization-log
```

**Đầu ra:** Bản text cuối cùng an toàn logic + Cổng API sẵn sàng cho Phase 4 gọi.

---

## 3. Dependency Map

```
Verified Text Pack (Phase 2)
        │
        ▼
Task #p3.1 (Entity Graph Construction)
        │           ▲
        ▼           │  LLM builds nodes/edges
Task #p3.2 (Localization Agent) ◀──────┐
        │                               │  REJECT → rethink
        ▼                               │
Task #p3.3 (Butterfly Validator) ──────┘
        │           ▲
        │           │  Algo only (BFS/DFS)
        │  ACCEPT   │
        ▼
Task #p3.4 (Mutation & API Handoff)
        │
        ▼
    Phase 4
```

---

## 4. Lưu ý quan trọng cho Partners

1. **Butterfly Validator phải chạy trong mili-giây** — đây là lý do dùng BFS/DFS thuần thay vì gọi LLM.
2. **Entity Graph là cấu trúc cốt lõi** — thiết kế tốt cấu trúc này sẽ quyết định hiệu năng toàn Phase 3.
3. **Localization Log** phải được lưu riêng — Phase 5 (QA) sẽ dùng log này để đối soát Butterfly Effect toàn cục.
4. Tọa độ bbox phải được **giữ nguyên** xuyên suốt — Phase 4 cần mapping chính xác text ↔ vị trí trên trang.
