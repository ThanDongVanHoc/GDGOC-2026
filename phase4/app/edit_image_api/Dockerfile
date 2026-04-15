FROM nvidia/cuda:11.8.0-base-ubuntu22.04

# Thiết lập biến môi trường để không bị hỏi timezone khi cài đặt các package
ENV DEBIAN_FRONTEND=noninteractive

# Update và cài đặt python3, pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Tạo working directory
WORKDIR /app

# (Tuỳ chọn) Gỡ bỏ các bản PyTorch cũ nếu có
RUN pip3 uninstall -y torch torchvision torchaudio

# Cài đặt PyTorch với CUDA 11.8
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copy file requirements
COPY requirements.txt .

# Cài đặt các thư viện cần thiết
RUN pip3 install -r requirements.txt

# Copy source code vào container
COPY main.py .

# Expose port (theo main.py)
EXPOSE 4206

# Lệnh chạy khi start container
CMD ["python3", "main.py"]
