# Sử dụng base image là PyTorch có sẵn CUDA 12.1 (Tối ưu cho H100)
FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

# Thiết lập biến môi trường
ENV DEBIAN_FRONTEND=noninteractive

# Cài đặt các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    git \
    wget \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /workspace

# Clone mã nguồn ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git

WORKDIR /workspace/ComfyUI

# Cài đặt thư viện Python của ComfyUI
RUN pip install --no-cache-dir -r requirements.txt

# ---
# LƯU Ý KHI TRIỂN KHAI THỰC TẾ:
# Docker này được thiết kế KHÔNG chứa file Model (Safetensors, Checkpoints) cực nặng.
# Khi thuê máy (Runpod/Vast.ai), hãy gắn (Mount) một ổ đĩa mạng chứa model 
# vào đường dẫn `/workspace/ComfyUI/models` để tự động nhận dạng Model.
# ---

# Mở cổng mặc định
EXPOSE 8188

# Lệnh khởi chạy server ComfyUI
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
