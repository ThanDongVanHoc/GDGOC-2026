#!/bin/bash
# Script triển khai tự động ComfyUI (Dành cho Ubuntu/Debian)

# Dừng thưc thi nếu có lỗi
set -e

echo "============================================="
echo "   BẮT ĐẦU CÀI ĐẶT COMFYUI VÀ DEPENDENCIES   "
echo "============================================="

# Cấu hình SUDO nếu không phải là root
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  else
    echo "Trình cài đặt yêu cầu quyền root. Vui lòng chạy dưới quyền root (su) hoặc cài đặt sudo."
    exit 1
  fi
fi

# 1. Cài đặt các thư viện hệ thống cần thiết
echo "[1/4] Cập nhật hệ thống và cài đặt system dependencies..."
$SUDO apt-get update
$SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y git wget python3-pip python3-venv libgl1 libglib2.0-0

# 2. Clone mã nguồn
echo "[2/4] Đang clone tải mã nguồn ComfyUI..."
if [ ! -d "ComfyUI" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
else
    echo "Thư mục ComfyUI đã tồn tại, bỏ qua bước clone."
fi

cd ComfyUI

# 3. Tạo virtual environment (Tùy chọn, rất khuyên dùng)
echo "[3/4] Cài đặt Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 4. Cài đặt PyTorch và các thư viện
echo "[4/4] Cài đặt các thư viện Python cần thiết (bao gồm Torch)..."
# Tối ưu cho H100 chạy CUDA 12.1+
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Cài đặt thư viện của ComfyUI
pip install --no-cache-dir -r requirements.txt

echo "============================================="
echo "          CÀI ĐẶT HOÀN TẤT THÀNH CÔNG        "
echo "============================================="
echo ""
echo "Để khởi chạy ComfyUI, hãy chạy các lệnh sau:"
echo "  cd ComfyUI"
echo "  source venv/bin/activate"
echo "  python main.py --listen 0.0.0.0 --port 8188"