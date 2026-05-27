#!/usr/bin/env bash
# EC2 Ubuntu 22.04에서 SSH 접속 후 한 번만 실행
# Usage: bash scripts/ec2_setup.sh
set -euo pipefail

REPO="https://github.com/parksehyn/AiSecurity.git"
APP_DIR="$HOME/AiSecurity"

# --- Docker ---
echo "[setup] Docker 설치..."
sudo apt-get update -q
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo usermod -aG docker "$USER"

# --- 컨테이너 기동 (sudo로 실행 — 그룹 재로그인 불필요) ---
echo "[setup] nginx, redis 컨테이너 시작..."
sudo docker run -d --name nginx --restart unless-stopped nginx:alpine
sudo docker run -d --name redis --restart unless-stopped redis:alpine
echo "[setup] 컨테이너 상태:"
sudo docker ps --format "  {{.Names}}\t{{.Status}}"

# --- Falco ---
echo "[setup] Falco 설치..."
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc \
    | sudo gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
https://download.falco.org/packages/deb stable main" \
    | sudo tee /etc/apt/sources.list.d/falcosecurity.list
sudo apt-get update -q
sudo apt-get install -y falco

# --- 레포 클론 ---
echo "[setup] 레포 클론..."
git clone -b main "$REPO" "$APP_DIR"

# --- Python venv ---
echo "[setup] Python 가상환경 생성 및 패키지 설치..."
sudo apt-get install -y python3-venv
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# --- Falco 드라이버 설치 및 시작 ---
echo "[setup] Falco 드라이버 설치..."
sudo falcoctl driver install
echo "[setup] Falco 시작..."
sudo falco \
    -o engine.kind=modern_ebpf \
    -o json_output=true \
    -o file_output.enabled=true \
    -o "file_output.filename=$HOME/falco_raw.log" \
    -o file_output.keep_alive=false \
    2>/dev/null &
sleep 5
echo "[setup] Falco PID: $(pgrep falco || echo 'not found')"

echo ""
echo "[setup] 완료."
echo "  docker 그룹 적용을 위해 재접속 후 아래 명령 실행:"
echo ""
echo "  nohup bash '$APP_DIR/data_collection/collect_loop.sh' 20 >> \$HOME/collect.log 2>&1 &"
echo "  tail -f ~/collect.log"
