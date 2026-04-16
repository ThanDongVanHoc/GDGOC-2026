# Hướng dẫn Deploy ComfyUI bằng Docker cho H100 (Không kèm Model)

Đây là file Docker rút gọn (Lightweight) chỉ chứa Source code và các thư viện cần thiết để chạy ComfyUI. Model sẽ do người dùng tự xử lý bằng cách mount Volume.

## 1. Cách Build và Push Image lên máy cục bộ

Mở terminal tại thư mục này (`comfyui_deploy`) và chạy các lệnh sau:

### Build Image
```bash
docker build -t <ten_dockerhub_cua_ban>/comfyui-light:latest .
```
*(Thay `<ten_dockerhub_cua_ban>` bằng username Docker Hub của bạn)*

### Push lên mạng (Tùy chọn)
Nếu bạn định dùng Image này trên các dịch vụ Cloud như Runpod hoặc Vast.ai:
```bash
docker push <ten_dockerhub_cua_ban>/comfyui-light:latest
```

## 2. Cách Chạy (Run) và Tích hợp Model

Thay vì tải Model thẳng vào Docker, bạn hãy làm theo mô hình này:

### Nếu chạy ở Local:
Bạn có sẵn một thư mục chứa Model ở máy của mình (Ví dụ: `/home/user/my_models`). Khi đó chạy lệnh:

```bash
docker run -d \
    --gpus all \
    -p 8188:8188 \
    -v /home/user/my_models:/workspace/ComfyUI/models \
    <ten_dockerhub_cua_ban>/comfyui-light:latest
```

### Nếu chạy ở Cloud (Ví dụ Runpod):
1. **Thuê 1 Network Volume** (Ví dụ đặt tên là `ComfyUI-Models-Data`).
2. Trong phần tạo máy H100:
   - Mục **Container Image**: Ghi `ten_dockerhub_cua_ban/comfyui-light:latest`
   - Mục **Volume Mount**: Mount cục `ComfyUI-Models-Data` vào đường dẫn `/workspace/ComfyUI/models` của container.
3. Chạy máy, và copy file Model vào volume đó 1 lần duy nhất trong đời. Những lần tạo máy H100 sau, chỉ cần mount lại cục volume đó là xong.
