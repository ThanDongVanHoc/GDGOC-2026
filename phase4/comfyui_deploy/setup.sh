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
echo "[1/5] Cập nhật hệ thống và cài đặt system dependencies..."
$SUDO apt-get update
$SUDO apt-get install -y software-properties-common
$SUDO add-apt-repository -y ppa:deadsnakes/ppa
$SUDO apt-get update
$SUDO apt-get install -y git wget python3.12 python3.12-venv python3.12-dev libgl1 libglib2.0-0

# 2. Clone mã nguồn
echo "[2/5] Đang clone tải mã nguồn ComfyUI..."
if [ ! -d "ComfyUI" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
else
    echo "Thư mục ComfyUI đã tồn tại, bỏ qua bước clone."
fi

cd ComfyUI

# 3. Tạo virtual environment (Tùy chọn, rất khuyên dùng)
echo "[3/5] Cài đặt Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3.12 -m venv venv
fi
source venv/bin/activate

# 4. Cài đặt PyTorch và các thư viện
echo "[4/5] Cài đặt các thư viện Python cần thiết (bao gồm Torch)..."
# Tối ưu cho H100 chạy CUDA 12.1+
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Cài đặt thư viện của ComfyUI
pip install --no-cache-dir -r requirements.txt

# Cài đặt ComfyUI-Manager
echo "Đang cài đặt ComfyUI-Manager..."
if [ ! -d "custom_nodes/ComfyUI-Manager" ]; then
    git clone https://github.com/Comfy-Org/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager
    if [ -f "custom_nodes/ComfyUI-Manager/requirements.txt" ]; then
        pip install --no-cache-dir -r custom_nodes/ComfyUI-Manager/requirements.txt
    fi
else
    echo "ComfyUI-Manager đã được cài đặt, bỏ qua."
fi

# Cài đặt Custom Nodes theo yêu cầu
echo "Đang tải các Custom Nodes (Impact Pack, CLIPSeg, ArtVenture)..."

# 1. ComfyUI-Impact-Pack
if [ ! -d "custom_nodes/ComfyUI-Impact-Pack" ]; then
    git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git custom_nodes/ComfyUI-Impact-Pack
    if [ -f "custom_nodes/ComfyUI-Impact-Pack/requirements.txt" ]; then
        pip install --no-cache-dir -r custom_nodes/ComfyUI-Impact-Pack/requirements.txt
    fi
fi

# 2. ComfyUI-CLIPSeg
if [ ! -d "custom_nodes/ComfyUI-CLIPSeg" ]; then
    git clone https://github.com/biegert/ComfyUI-CLIPSeg.git custom_nodes/ComfyUI-CLIPSeg
    if [ -f "custom_nodes/ComfyUI-CLIPSeg/requirements.txt" ]; then
        pip install --no-cache-dir -r custom_nodes/ComfyUI-CLIPSeg/requirements.txt
    fi
fi

# 3. comfyui-art-venture
if [ ! -d "custom_nodes/comfyui-art-venture" ]; then
    git clone https://github.com/sipherxyz/comfyui-art-venture.git custom_nodes/comfyui-art-venture
    if [ -f "custom_nodes/comfyui-art-venture/requirements.txt" ]; then
        pip install --no-cache-dir -r custom_nodes/comfyui-art-venture/requirements.txt
    fi
fi

# 5. Tải các model cần thiết
echo "[5/5] Đang tải các model cần thiết..."
mkdir -p models/diffusion_models models/loras models/text_encoders models/vae
wget -nc https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors -P models/diffusion_models/
wget -nc https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors -P models/loras/
wget -nc https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors -P models/text_encoders/
wget -nc https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors -P models/vae/

echo "============================================="
echo "          CÀI ĐẶT HOÀN TẤT THÀNH CÔNG        "
echo "============================================="
echo ""
echo "Để khởi chạy ComfyUI, hãy chạy các lệnh sau:"
echo "  cd ComfyUI"
echo "  source venv/bin/activate"
echo "  python main.py --listen 0.0.0.0 --port 8888"