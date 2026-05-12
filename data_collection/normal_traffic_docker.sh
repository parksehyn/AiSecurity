#!/usr/bin/env bash
set -euo pipefail

NGINX_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' nginx)
echo "[normal_traffic] nginx=$NGINX_IP"
echo "[normal_traffic] 시작: $(date '+%Y-%m-%d %H:%M:%S')"

docker run --rm alpine sh -c "apk add -q apache2-utils && ab -n 5000 -c 10 http://${NGINX_IP}/" > /dev/null 2>&1 &

for i in $(seq 1 200); do
    KEY="key:$((RANDOM % 100))"
    docker exec redis redis-cli SET "$KEY" "value_$i" > /dev/null
    docker exec redis redis-cli GET "$KEY" > /dev/null
    sleep 0.$((RANDOM % 5 + 1))
done &

wait
echo "[normal_traffic] 완료: $(date '+%Y-%m-%d %H:%M:%S')"
