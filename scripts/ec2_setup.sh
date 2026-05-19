#!/usr/bin/env bash
# EC2 Ubuntu 22.04에서 SSH 접속 후 한 번만 실행
# Usage: bash scripts/ec2_setup.sh
set -euo pipefail

REPO="https://github.com/parksehyn/AiSecurity.git"
APP_DIR="$HOME/AiSecurity"

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
git clone -b feature/data-collection "$REPO" "$APP_DIR"

# --- Python venv ---
echo "[setup] Python 가상환경 생성 및 패키지 설치..."
sudo apt-get install -y python3-venv
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

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
