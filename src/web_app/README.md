# Web Application UI - Sách: Re-engineering Agent

Hệ thống giao diện Web này được sinh ra nhằm mục đích tạo lập một Trạm phân tích (Interactive Explorer) cho quy trình dịch thuật và tái kiến thiết Sách. 

Nguyên tắc thiết kế hệ thống là theo đúng mô hình **Single-Page Application (SPA)** siêu mượt mà kết hợp với kiến trúc **Modular Controller** hiện đại, tách biệt hoàn toàn giữa Xử lý Logic (Backend) và Hiển thị (Frontend).

---

## 1. Kiến trúc hệ thống (Architecture)

Chương trình được phát triển theo mẫu kiến trúc **Flask Blueprint Architecture** kết hợp với **Application Factory Pattern**:
1. **Application Factory (`__init__.py`)**: Hàm `create_app` sinh ra thể hiện của Flask. Tránh để lộ Global Context nhằm đảm bảo có thể mở rộng (scale up) hoặc khởi tạo theo từng Môi trường đa dạng cực kì tốt (Dev/Prod/Test) mà không gây chập chờn xung đột (Circular imports).
2. **RESTful API Blueprint (`api.py`)**: Đóng vai trò là cỗ máy Backend thuần túy, chỉ nhận file (`upload`) và ói ra cấu trúc JSON hoặc hình ảnh (Không dính líu đến HTML).
3. **Frontend Route Blueprint (`pages.py`)**: Điểm chạm duy nhất của Web App. Nó chỉ khởi tạo bộ khung xương UI lên Client 1 lần duy nhất lúc vừa vào trang web.

---

## 2. Cấu trúc thư mục (Folder Structure)

```text
src/web_app/
│
├── __init__.py           # Application Factory: Build cấu hình core Flask app và trích xuất Absolute Path
├── config.py             # Class chứa các Hằng số (Constants), Path và Keys
│
├── routes/               # Quản lý Blueprint Controllers
│   ├── __init__.py       # Export Blueprint instances
│   ├── pages.py          # Controller xử lý routing Frontend rỗng (chỉ render HTML Layout)
│   └── api.py            # Controller xử lý Logic Backend API (Post Upload, Get Image Buffer)
│
├── static/               # File Tĩnh Client-Side (CSS/JS)
│   ├── css/
│   │   └── style.css     # Định nghĩa Premium UI, Dark-theme, Glassmorphism, Bounding Boxes
│   └── js/
│       └── main.js       # Core JS Logic (Fetch API, Mapping Tọa độ, Tính toán Tỷ lệ % Highlight Box)
│
└── templates/
    └── index.html        # Giao diện xương sống (Không chứa logic)
```

---

## 3. Công nghệ sử dụng (Tech Stack)

### Backend Engine
- **Môi trường:** `Python 3.x`
- **Framework Chính:** `Flask` (Blueprint Modularity, Application Factory)
- **Cơ chế truyền tải Data:** `flask.jsonify`, HTTP API, `flask.Response` (Image buffer binarary stream)
- **Thư viện Xử lý PDF:** `PyMuPDF` (Fitz) -> Siêu việt trong việc bóc tách Layout Text/Image Object và vẽ Document sang ảnh số (Rasterization).

### Frontend UI
- **Giao diện:** Semantic `HTML5` và `CSS3` Vanilla.
- **Phong cách Layout:** `Dark mode`, Khối kính mờ `Glassmorphism`, `CSS Grid` Split-view chia tỉ lệ.
- **Interactive Component:** JavaScript (`Vanilla JS`) - Tương tác DOM trực tiếp thông suốt, `Fetch API` để gọi dữ liệu JSON bất đồng bộ (AJAX).
- **Trực quan PDF (Visualization):** Thuật toán tính toán Tọa độ điểm ảo ngầm - Quy đổi tọa độ Pixel Point của hệ thống sách sang hệ tọa độ Phần trăm `%` (Left, Top, Width, Height) để Bounding Box luôn co giãn và hiển thị chính xác mọi không gian màn hình.

---

## 4. Dòng chảy Logic (Application Flow & Logic)

Dưới đây vòng đời một truy vấn chạy trong Web App:

1. **Khởi chạy Hệ thống:** 
   - Lệnh `python run_server.py` kích hoạt `create_app()`. Flask mount các thẻ Blueprint và các cấu hình tĩnh. Chờ Request ở `http://localhost:5000`.
   - Người dùng truy cập Browser -> `pages.py` trả về `index.html` và Browser tải `style.css` + `main.js`. Web load thành công 1 lần duy nhất, **không bao giờ cần tải lại trang nữa**.

2. **Up File (User Action):** 
   - Người dùng Kéo & Thả file PDF vào thùng chứa Drop-zone trên Front-end.
   - JS `fetch()` gửi nguyên rập cục File đó (FormData) đẩy về route `[POST] /api/upload`.

3. **Backend Xử lý (Agent Parse):**
   - API Blueprint nhận diện tệp -> Lưu tĩnh tạm vào `input_pdfs/`.
   - Gọi thẳng Core Phase 4 của Agent: `annotate_pdf_blocks(input_path, output_path)`.
   - Engine PyMuPDF bung file, bóc tách ra các block Text và Image theo định dạng Tọa độ Không gian. 
   - Backend đóng gói nó dưới dạng 1 Mảng Object Schema JSON -> Trả thẳng cục JSON về Front-end phản hồi truy vấn HTTP thành công.

4. **Frontend Hiển thị & Đồng bộ View (DOM Updating):**
   - JS nhận được Cục JSON -> Xóa hiệu ứng Loading, bật màn hình Split-view `grid`.
   - **Bên Trái (PDF Visuals):** Tạo các thẻ `<img>` chọc qua Route `/api/page_image/...` lấy toàn bộ nội dung PDF thành Ảnh.
   - Vòng lặp đẻ ra hàng tỉ ô Khung `<div class="bbox-overlay">` ốp chìm vào mặt ảnh, tính toán vị trí tuyệt đối (Absolute) dựa trên công thức `(box_coordinates / page_width) * 100`.
   - **Bên Phải (JSON Visuals):** Tạo các thẻ Code JSON với String được bọc thành Code Color cực đẹp. Cài cắm hàng loạt Identity Node liên thông vói `Bbox` bên trái.

5. **Phản hồi Tương tác (Click-to-Highlight Interactivity):**
   - Click vô vùng Khung tranh phía PDF (Trái) -> JS Bắt được Event của ID đó -> Kích hoạt Class `active-highlight` (phát sáng Vàng).
   - Truyền tín hiệu gọi lệnh `scrollIntoView()` nhắm thẳng tới Code Block đồng dạng ở nửa Cột Phải (JSON). Màn hình Right-Panel tự động trượt siêu tốc tới dòng Code mang giá trị của khung ảnh vừa nhấp. End flow!
   
---

## 5. Tài liệu API (API Specification)

Hệ thống cung cấp các endpoint sau theo chuẩn RESTful nhằm phục vụ hiển thị UI và phân tích dữ liệu nguyên liệu tải lên. Nơi tiêu thụ các API này là các module JavaScript từ phía Frontend.

---

### 1. Phục vụ Giao diện (Entry Point)

#### `GET /`
- **Mô tả:** Trả về giao diện khởi nguyên của ứng dụng Single-Page Application (SPA).
- **Request parameters:** None.
- **Responses:**
  - `200 OK`: File giao diện `index.html` với header `Content-Type: text/html`.

---

### 2. Xử lý Dữ liệu (Processing APIs)

#### `POST /api/upload`
- **Mô tả:** Cổng tiếp nhận (Ingestion point) file PDF upload. Khi nhận file, nó sẽ khởi chạy Engine bóc tách (Agent Phase 4) để cào cấu trúc nội dung.
- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  | Tên Field | Kiểu dữ liệu | Bắt buộc | Mô tả |
  | :--- | :--- | :--- | :--- |
  | `pdf` | `File` | Yes | File tài liệu định dạng PDF cần được nhận dạng cấu trúc |
- **Responses:**
  - **`200 OK` (Thành công):** Application/JSON. Trả về cấu trúc layout theo từng trang (kèm kích thước thực tế) và danh sách các Object block của PDF.
    ```json
    {
      "success": true,
      "json_data": [
        {
          "page_id": 1,
          "width": 595.27,
          "height": 841.89,
          "text_blocks": [
            {
              "content": "Đoạn văn bản trích xuất mẫu",
              "bbox": [67.3, 45.2, 530.1, 80.5]
            }
          ],
          "image_blocks": [
            {
              "bbox": [120.0, 300.0, 400.0, 500.0]
            }
          ]
        }
      ]
    }
    ```
  - **`400 Bad Request` / `500 Internal Server Error` (Thất bại):** Application/JSON.
    ```json
    {
      "success": false,
      "error": "Chi tiết lý do lỗi (Ví dụ: Định dạng file không hợp lệ)"
    }
    ```

---

#### `GET /api/page_image/<filename>/<page_id>`
- **Mô tả:** Endpoint render ảnh học (Rasterization Engine). Nhận yêu cầu và trích xuất một trang PDF cụ thể thành hình ảnh ma trận điểm ảnh (PNG) giúp Frontend hiển thị làm nền tham chiếu các vùng chọn màu sáng.
- **Path Parameters:**
  | Tham số | Kiểu dữ liệu | Bắt buộc | Mô tả |
  | :--- | :--- | :--- | :--- |
  | `filename` | `String` | Yes | Tên gốc của file PDF đã upload vào hệ thống trước đó |
  | `page_id` | `Integer` | Yes | Chỉ mục trang (Index tự nhiên bắt đầu từ `1`) |
- **Responses:**
  - `200 OK`: Chuỗi binary nhị phân với header `Content-Type: image/png`. Trình duyệt lập tức hiểu và vẽ ảnh.
  - `404 Not Found`: Plaintext text/plain. (Ví dụ: "File not found" hoặc "Page out of range").
  - `500 Internal Server Error`: Plaintext text/plain cảnh báo lỗi thư viện engine phân giải file PDF rớt.

---
*Phát triển bởi mô hình chuẩn Agentic Concept.*
