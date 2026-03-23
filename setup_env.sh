#!/usr/bin/env bash
set -Eeuo pipefail

VENV_DIR="wkshp_env"
PYTHON_BIN="python3"
PYTORCH_VERSION="2.7.1"
TORCHVISION_VERSION="0.22.1"
TORCHAUDIO_VERSION="2.7.1"
PYTORCH_INDEX_URL="https://download.pytorch.org/whl/cu128"

log() {
  echo "[$(date +'%H:%M:%S')] $*"
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

log "Starting environment setup..."

require_cmd bash
require_cmd "$PYTHON_BIN"
require_cmd sudo
require_cmd apt-get

if grep -qi microsoft /proc/version 2>/dev/null; then
  log "WSL environment detected."
else
  log "Warning: this does not look like WSL :-/ Continuing anyway."
fi

log "Checking NVIDIA GPU visibility from WSL..."
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi || true
else
  log "Warning: nvidia-smi not found in PATH."
  log "Make sure the NVIDIA Windows driver with WSL support is installed on the Windows host."
fi

if [ -d "/usr/lib/wsl/lib" ]; then
  log "WSL GPU support libraries detected at /usr/lib/wsl/lib."
else
  log "Warning: /usr/lib/wsl/lib not found. GPU passthrough may not be configured."
fi

log "Installing required system packages..."
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3-venv \
  python3-pip \
  ffmpeg \
  git \
  build-essential \
  cmake \
  ninja-build \
  pkg-config \
  curl

if [ ! -d "$VENV_DIR" ]; then
  log "Creating virtual environment in $VENV_DIR ..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  log "Virtual environment already exists: $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

log "Upgrading pip/setuptools/wheel..."
pip install --upgrade pip setuptools wheel

log "Installing PyTorch with CUDA wheels..."
pip install \
  "torch==${PYTORCH_VERSION}" \
  "torchvision==${TORCHVISION_VERSION}" \
  "torchaudio==${TORCHAUDIO_VERSION}" \
  --index-url "$PYTORCH_INDEX_URL"

log "Installing Python application dependencies..."
pip install -r requirements.txt

log "Installing OuteTTS with CUDA-enabled llama.cpp bindings..."
CMAKE_ARGS="-DGGML_CUDA=on" pip install --upgrade outetts

log "Running verification checks..."
python - <<'PY'
import os
import shutil
import sys

print("Python:", sys.version)
print("ffmpeg in PATH:", shutil.which("ffmpeg"))

try:
    import torch
    print("torch version:", torch.__version__)
    print("cuda available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("gpu name:", torch.cuda.get_device_name(0))
        print("gpu count:", torch.cuda.device_count())
except Exception as exc:
    print("torch verification failed:", exc)

try:
    import outetts
    print("outetts version:", getattr(outetts, "__version__", "unknown"))
except Exception as exc:
    print("outetts import failed:", exc)
PY

mkdir models

log "Setup complete."
log "Activate the environment with: source ${VENV_DIR}/bin/activate"

source wkshp_env/bin/activate
python3 dl_hf_model.py --token [HUGGINGFACE_TOKEN_HERE] --model unsloth/Llama-OuteTTS-1.0-1B
