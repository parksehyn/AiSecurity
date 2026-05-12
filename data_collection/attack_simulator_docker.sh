#!/usr/bin/env bash
set -euo pipefail

TARGET="nginx"
jitter() { sleep $(( RANDOM % ($2 - $1 + 1) + $1 )); }

echo "[T1609] Shell Exec 시작: $(date '+%Y-%m-%d %H:%M:%S')"
CMDS=("id" "whoami" "uname -a" "ps aux" "env" "cat /etc/hostname")
for i in $(seq 1 30); do
    CMD=${CMDS[$((RANDOM % ${#CMDS[@]}))]}
    docker exec $TARGET sh -c "$CMD" > /dev/null 2>&1 || true
    jitter 1 3
done
echo "[T1609] 완료: $(date '+%Y-%m-%d %H:%M:%S')"

sleep $((RANDOM % 10 + 10))

echo "[T1552] Sensitive File Access 시작: $(date '+%Y-%m-%d %H:%M:%S')"
TARGETS=("*.key" "*.pem" "*.env" "*.crt" "id_rsa" "*.secret")
for i in $(seq 1 50); do
    T=${TARGETS[$((RANDOM % ${#TARGETS[@]}))]}
    docker exec $TARGET find / -name "$T" 2>/dev/null || true
    jitter 1 5
done
echo "[T1552] 완료: $(date '+%Y-%m-%d %H:%M:%S')"

sleep $((RANDOM % 10 + 10))

echo "[T1611] Privilege Escalation 시작: $(date '+%Y-%m-%d %H:%M:%S')"
PRIV_CMDS=("cat /proc/1/environ" "ls /proc/1/root" "mount" "cat /etc/shadow" "cat /etc/passwd")
for i in $(seq 1 25); do
    CMD=${PRIV_CMDS[$((RANDOM % ${#PRIV_CMDS[@]}))]}
    docker exec $TARGET sh -c "$CMD" > /dev/null 2>&1 || true
    jitter 1 4
done
echo "[T1611] 완료: $(date '+%Y-%m-%d %H:%M:%S')"

echo "[attack_sim] 완료: $(date '+%Y-%m-%d %H:%M:%S')"
