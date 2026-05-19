#!/usr/bin/env bash
# 정상 트래픽 → 공격 시뮬레이션을 반복하며 공격 윈도우를 파일에 기록한다.
# Usage: bash collect_loop.sh [ROUNDS]
#   ROUNDS: 공격 라운드 수 (기본 20)
# 출력: ~/attack_windows.txt  (auto_labeling.py --attack-windows 에 그대로 전달)

set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
WINDOWS_FILE="$HOME/attack_windows.txt"
NORMAL_SECS=600   # 공격 사이 정상 트래픽 시간 (초)
ROUNDS=${1:-20}

> "$WINDOWS_FILE"
echo "[collect_loop] 시작: $(date '+%Y-%m-%d %H:%M:%S'), ${ROUNDS}라운드"

for round in $(seq 1 "$ROUNDS"); do
    echo "[round $round/$ROUNDS] 정상 트래픽 (${NORMAL_SECS}s)..."
    END=$(( $(date +%s) + NORMAL_SECS ))
    while [ "$(date +%s)" -lt "$END" ]; do
        bash "$DIR/normal_traffic_docker.sh" > /dev/null 2>&1 || true
    done

    ATTACK_START=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[round $round/$ROUNDS] 공격 시작: $ATTACK_START"
    bash "$DIR/attack_simulator_docker.sh" > /dev/null 2>&1 || true
    ATTACK_END=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[round $round/$ROUNDS] 공격 완료: $ATTACK_END"

    echo "${ATTACK_START},${ATTACK_END}" >> "$WINDOWS_FILE"
done

echo "[collect_loop] 완료. 데이터 처리 시작..."

python3 "$DIR/falco_to_csv.py" --input "$HOME/falco_raw.log" --output "$HOME/events.csv"

mapfile -t WINDOWS < "$WINDOWS_FILE"
WINDOWS_ARGS=()
for w in "${WINDOWS[@]}"; do
    WINDOWS_ARGS+=("$w")
done

python3 "$DIR/auto_labeling.py" \
    --input "$HOME/events.csv" \
    --output "$HOME/labeled.csv" \
    --attack-windows "${WINDOWS_ARGS[@]}"

echo "[collect_loop] labeled.csv 생성 완료 → $HOME/labeled.csv"
