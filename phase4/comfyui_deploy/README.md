# Hướng dẫn Deploy ComfyUI (Dành cho Máy chủ Cloud GPU)

Đây là script tự động (bash script) nhằm giúp bạn triển khai ComfyUI lên các máy chủ chuyên GPU (như H100 chạy trên Runpod, Vast.ai, AWS) vô cùng dễ dàng mà không cần phải đóng gói qua Docker như trước đây.

Script sẽ tự động:
- Cài đặt các thư viện hệ thống cần thiết.
- Tải toàn bộ source gốc ComfyUI mới nhất.
- Tạo Virtual Environment để không ảnh hưởng đến package hệ thống.
- Cài đặt PyTorch tương thích tối đa với CUDA 12.1 (Tối ưu cho dòng RTX thế hệ mới, A100, H100).
- Cài đặt các thư viện yêu cầu trong `requirements.txt`.

## 1. Hướng dẫn cài đặt

Di chuyển vào thư mục này (`comfyui_deploy`) trên máy chủ cloud của bạn và cấp quyền thực thi cho script:

```bash
chmod +x setup.sh
./setup.sh
```

*(Lưu ý: Quá trình cài đặt có thể mất vài phút vì phải tải Torch và clone mã nguồn).*

## 2. Khởi chạy và truy cập ComfyUI

Sau khi cài đặt xong, bạn có thể kích hoạt môi trường đã được cài và khởi chạy server ngay:

```bash
cd ComfyUI
source venv/bin/activate
python main.py --listen 0.0.0.0 --port 8188
```

- Lệnh này sẽ mở ứng dụng trên cổng `8188`. 
- Cờ `--listen 0.0.0.0` để có thể truy cập qua IP public của máy ảo.
- Bạn có thể vào Web UI bằng trình duyệt thông qua địa chỉ: `http://<IP public của máy>:8188`

## 3. Quản lý Models & Data

- Nếu là máy **Local** hoặc một máy cố định, bạn có thể trực tiếp copy files checkpont/safetensors vào thư mục `ComfyUI/models`.
- Nếu dùng **Cloud (Runpod/Vast/...)**, thường ổ đĩa cài OS (Root Volume) thường hay bị xóa sau khi thuê lại hoặc dung lượng nhỏ. Tốt nhất là bạn hãy có một **Network Disk** (Volume dự phòng) và dùng lệnh Symlink sang đường dẫn models của ComfyUI (Ví dụ: `ln -s /workspace/network_volume/models /workspace/ComfyUI/models`). Bằng cách này model nặng hàng chục GB sẽ tồn tại độc lập ở Network volume.
