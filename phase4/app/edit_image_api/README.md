# Qwen Image Edit API

Dự án này cung cấp một API (dựa trên **FastAPI**) để chỉnh sửa hình ảnh bằng cách sử dụng mô hình AI **Qwen-Image-Edit** từ Hugging Face.

Toàn bộ hệ thống có thể được ảo hoá và chạy linh hoạt trên các máy chủ có GPU NVIDIA (như H100) thông qua **Docker**.

---

## 🛠 Yêu cầu hệ thống (Prerequisites)

- Máy chủ Ubuntu có GPU NVIDIA (VRAM tối thiểu > 16GB, khuyến nghị các dòng cao như A100, H100).
- Đã cài đặt [Docker](https://docs.docker.com/engine/install/ubuntu/) và [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) để Docker nhận dạng GPU.
- NVIDIA Driver hỗ trợ CUDA 11.8 trở lên.

---

## 🚀 Hướng dẫn Cài đặt & Chạy với Docker

### 1. Build Docker Image
Mở terminal và trỏ đến thư mục chứa source code, sau đó tiến hành đóng gói Docker image:
```bash
docker build -t qwen-api .
```
*(Quá trình build có thể mất vài phút tuỳ thuộc vào tốc độ mạng và dung lượng GPU model)*

### 2. Khởi chạy Server
Chạy container ngầm phía dưới (detach) và gắn quyền truy cập toàn bộ GPU bằng thuộc tính `--gpus all`.
```bash
docker run -d --gpus all -p 4206:4206 --name qwen_server qwen-api
```

### 3. Kiểm tra Logs
Quá trình load Model (gần ~10GB checkpoint) cần từ 10 - 20s. Bạn có thể kiểm tra xem API đã khởi động xong chưa:
```bash
docker logs -f qwen_server
```
API đã sẵn sàng khi bạn thấy dòng: `Uvicorn running on http://0.0.0.0:4206`.

---

## 💻 Cách sử dụng (Test API)

Bạn có thể gọi trực tiếp API này qua Postman hoặc sử dụng lệnh `curl`.  

**Ví dụ `curl` Endpoint:** (Post form data với một hình ảnh `input.png`):

```bash
curl -X POST "http://localhost:4206/edit-image/" \
  -F "file=@input.png" \
  -F "prompt=Make the weather look like a sunny day" \
  --output result.png
```
Lệnh trên sẽ gửi file ảnh, xử lý và lưu hình ảnh trả về trực tiếp thành file `result.png`.

---

## ⚠️ Lưu ý Quan Trọng

1. **Hiệu năng (Performance)**: Mô hình đang được nạp dưới dạng `torch.bfloat16` trên CUDA. Để tối ưu inference trên H100 hoặc A100, hãy đảm bảo bạn bật `--gpus all` khi run docker, nếu không quá trình gen ảnh sẽ gặp lỗi CPU.
2. **Dung lượng (Storage)**: `Dockerfile` tải rất nhiều framework AI đắt đỏ. Hãy đảm bảo ổ mềm của bạn có ít nhất `20GB` trống.
3. **Cập nhật Port**: Mặc định FastAPI đang lắng nghe ở port `4206`. Hãy mở (allow) port này trên Firewall/Security Groups của máy chủ nếu muốn public trên IP tĩnh.
