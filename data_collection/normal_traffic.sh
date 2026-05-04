#!/usr/bin/env bash
# 정상 트래픽 생성 — nginx / redis / webapp 대상
# 실행 전제: minikube 내부에서 실행, kubectl 접근 가능

set -euo pipefail

NGINX_POD=$(kubectl get pod -l app=nginx -o jsonpath='{.items[0].metadata.name}')
REDIS_POD=$(kubectl get pod -l app=redis -o jsonpath='{.items[0].metadata.name}')
WEBAPP_POD=$(kubectl get pod -l app=webapp -o jsonpath='{.items[0].metadata.name}')

NGINX_IP=$(kubectl get pod "$NGINX_POD" -o jsonpath='{.status.podIP}')
REDIS_IP=$(kubectl get pod "$REDIS_POD" -o jsonpath='{.status.podIP}')

echo "[normal_traffic] nginx=$NGINX_IP  redis=$REDIS_IP"
echo "[normal_traffic] 정상 트래픽 생성 시작: $(date '+%Y-%m-%d %H:%M:%S')"

# ── nginx: HTTP 요청 ──────────────────────────────────────────────────────────
echo "[normal_traffic] nginx HTTP 트래픽 생성 중..."
kubectl exec "$NGINX_POD" -- ab -n 10000 -c 10 "http://${NGINX_IP}/" > /dev/null 2>&1 &

# ── redis: 기본 명령 반복 ─────────────────────────────────────────────────────
echo "[normal_traffic] redis 명령 생성 중..."
for i in $(seq 1 500); do
    KEY="key:$((RANDOM % 100))"
    kubectl exec "$REDIS_POD" -- redis-cli SET "$KEY" "value_$i" > /dev/null
    kubectl exec "$REDIS_POD" -- redis-cli GET "$KEY" > /dev/null
    sleep 0.$(( RANDOM % 5 + 1 ))
done &

# ── webapp: 다양한 엔드포인트 요청 ───────────────────────────────────────────
echo "[normal_traffic] webapp 요청 생성 중..."
ENDPOINTS=("/" "/health" "/api/status" "/api/data")
for i in $(seq 1 300); do
    EP=${ENDPOINTS[$((RANDOM % ${#ENDPOINTS[@]}))]}
    kubectl exec "$WEBAPP_POD" -- wget -q -O /dev/null "http://localhost${EP}" 2>/dev/null || true
    sleep 0.$(( RANDOM % 8 + 2 ))
done &

wait
echo "[normal_traffic] 완료: $(date '+%Y-%m-%d %H:%M:%S')"
