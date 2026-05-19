#!/usr/bin/env bash
# EC2 Ubuntu 22.04에서 SSH 접속 후 한 번만 실행
# Usage: bash scripts/ec2_setup.sh
set -euo pipefail

REPO="https://github.com/parksehyn/AiSecurity.git"
APP_DIR="$HOME/AiSecurity"

# --- Docker ---
echo "[setup] Docker 설치..."
sudo apt-get update -q
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update -q
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker "$USER"
sudo systemctl enable --now docker

# --- Falco ---
echo "[setup] Falco 설치..."
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc \
    | sudo gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
https://download.falco.org/packages/deb stable main" \
    | sudo tee /etc/apt/sources.list.d/falcosecurity.list
sudo apt-get update -q
sudo apt-get install -y falco

# --- Python ---
echo "[setup] Python 패키지 설치..."
sudo apt-get install -y python3-pip
pip3 install -r "$APP_DIR/requirements.txt" 2>/dev/null || true  # 레포 클론 후 재실행

# --- 레포 클론 ---
echo "[setup] 레포 클론..."
git clone "$REPO" "$APP_DIR"
pip3 install -r "$APP_DIR/requirements.txt"

# --- 컨테이너 시작 ---
echo "[setup] nginx, redis 컨테이너 시작..."
# usermod 후 소켓 권한 반영을 위해 sg 사용
sg docker -c "docker run -d --name nginx nginx:alpine || docker start nginx"
sg docker -c "docker run -d --name redis redis:alpine || docker start redis"
sleep 5

# --- Falco 시작 (Modern eBPF, JSON 출력) ---
echo "[setup] Falco 시작..."
sudo nohup falco --modern-bpf -o json_output=true >> "$HOME/falco_raw.log" 2>&1 &
sleep 3
echo "[setup] Falco PID: $(pgrep falco || echo 'not found')"

# --- 수집 루프 시작 ---
echo "[setup] 데이터 수집 루프 시작 (20라운드)..."
nohup bash "$APP_DIR/data_collection/collect_loop.sh" 20 >> "$HOME/collect.log" 2>&1 &

echo ""
echo "[setup] 완료. 진행 확인:"
echo "  tail -f ~/collect.log        # 수집 진행 상황"
echo "  tail -f ~/falco_raw.log      # Falco 원시 로그"
echo "  cat ~/attack_windows.txt     # 기록된 공격 윈도우"
