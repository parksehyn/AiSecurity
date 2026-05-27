#!/usr/bin/env bash
# Falco가 죽으면 자동으로 재시작하는 watchdog
# Usage: sudo bash scripts/falco_watchdog.sh &

REAL_HOME=$(getent passwd "${SUDO_USER:-$USER}" | cut -d: -f6)
LOG_FILE="${REAL_HOME}/falco_raw.log"
STDERR_FILE="${REAL_HOME}/falco_stderr.log"
INTERVAL=10  # 체크 주기 (초)

echo "[watchdog] 시작: $(date '+%Y-%m-%d %H:%M:%S')"

while true; do
    if ! pgrep -x falco > /dev/null; then
        echo "[watchdog] Falco 사망 감지 → 재시작: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$STDERR_FILE"
        falco \
            -o engine.kind=modern_ebpf \
            -o json_output=true \
            -o file_output.enabled=true \
            -o "file_output.filename=${LOG_FILE}" \
            -o file_output.keep_alive=false \
            >> "$STDERR_FILE" 2>&1 &
        sleep 5
    fi
    sleep "$INTERVAL"
done
