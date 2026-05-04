#!/usr/bin/env bash
# MITRE ATT&CK for Containers 공격 시뮬레이션 (4가지 시나리오)
# ⚠️  반드시 minikube 내부에서만 실행할 것 — 외부 네트워크 절대 금지
#
# 실행 후 attack_windows를 기록해 auto_labeling.py에 전달한다.
#
# Usage: bash attack_simulator.sh [target-pod]
#   target-pod: 공격 대상 pod 이름 (기본값: webapp pod)

set -euo pipefail

TARGET_POD=${1:-$(kubectl get pod -l app=webapp -o jsonpath='{.items[0].metadata.name}')}
NETWORK="$(kubectl get pod "$TARGET_POD" -o jsonpath='{.status.podIP}' | cut -d. -f1-3).0/24"

echo "[attack_sim] 대상 pod: $TARGET_POD"
echo "[attack_sim] 내부 서브넷: $NETWORK"

run_with_jitter() {
    # 각 반복 사이에 랜덤 sleep (1~5s) 추가
    local min=${1:-1} max=${2:-5}
    sleep $(( RANDOM % (max - min + 1) + min ))
}

# ── T1609: 컨테이너 내 셸 실행 ───────────────────────────────────────────────
echo ""
echo "[T1609] Shell Exec 시작: $(date '+%Y-%m-%d %H:%M:%S')"
CMDS=("id" "whoami" "uname -a" "ps aux" "env" "cat /etc/hostname")
for i in $(seq 1 30); do
    CMD=${CMDS[$((RANDOM % ${#CMDS[@]}))]}
    kubectl exec "$TARGET_POD" -- /bin/sh -c "$CMD" > /dev/null 2>&1 || true
    run_with_jitter 1 3
done
echo "[T1609] 완료: $(date '+%Y-%m-%d %H:%M:%S')"

run_with_jitter 10 20   # 시나리오 간 간격

# ── T1552: 민감 파일 접근 ────────────────────────────────────────────────────
echo ""
echo "[T1552] Sensitive File Access 시작: $(date '+%Y-%m-%d %H:%M:%S')"
TARGETS=("*.key" "*.pem" "*.env" "*.config" "*.crt" "id_rsa" "*.secret")
for i in $(seq 1 50); do
    TARGET=${TARGETS[$((RANDOM % ${#TARGETS[@]}))]}
    kubectl exec "$TARGET_POD" -- find / -name "$TARGET" 2>/dev/null || true
    run_with_jitter 1 5
done
echo "[T1552] 완료: $(date '+%Y-%m-%d %H:%M:%S')"

run_with_jitter 10 20

# ── T1046: 네트워크 스캔 ─────────────────────────────────────────────────────
echo ""
echo "[T1046] Network Scan 시작: $(date '+%Y-%m-%d %H:%M:%S')"
PORTS=("22" "80" "443" "3306" "5432" "6379" "8080" "9200")
for i in $(seq 1 20); do
    PORT=${PORTS[$((RANDOM % ${#PORTS[@]}))]}
    # nmap이 없을 경우 /dev/tcp fallback
    kubectl exec "$TARGET_POD" -- sh -c \
        "nmap -p $PORT $NETWORK 2>/dev/null || \
         (for h in 1 2 3 4 5; do \
            (echo >/dev/tcp/\${NETWORK%.*}.\$h/$PORT) 2>/dev/null && echo open; \
          done)" > /dev/null 2>&1 || true
    run_with_jitter 2 5
done
echo "[T1046] 완료: $(date '+%Y-%m-%d %H:%M:%S')"

run_with_jitter 10 20

# ── T1611: 권한 상승 시도 ────────────────────────────────────────────────────
echo ""
echo "[T1611] Privilege Escalation 시작: $(date '+%Y-%m-%d %H:%M:%S')"
ESCALATION_CMDS=(
    "nsenter --target 1 --mount -- ls /host 2>/dev/null"
    "cat /proc/1/environ 2>/dev/null"
    "ls /proc/1/root 2>/dev/null"
    "mount 2>/dev/null"
    "capsh --print 2>/dev/null"
)
for i in $(seq 1 25); do
    CMD=${ESCALATION_CMDS[$((RANDOM % ${#ESCALATION_CMDS[@]}))]}
    kubectl exec "$TARGET_POD" -- sh -c "$CMD" > /dev/null 2>&1 || true
    run_with_jitter 1 4
done
echo "[T1611] 완료: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo "[attack_sim] 전체 시뮬레이션 완료: $(date '+%Y-%m-%d %H:%M:%S')"
echo "[attack_sim] 위 시작/완료 시각을 attack_windows로 auto_labeling.py에 전달하세요."
