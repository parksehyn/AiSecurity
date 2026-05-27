# 데이터 수집 가이드 — VM에서 실행

## 전제 조건

- VirtualBox 실행 후 Ubuntu VM 부팅
- SSH: `ssh -p 2222 user32211690@127.0.0.1`

---

## Step 1 — 상태 확인

```bash
docker ps
pgrep -a falco
```

---

## Step 2 — 컨테이너 시작 (없을 때만)

```bash
docker rm -f nginx redis 2>/dev/null || true
docker run -d --name nginx --restart unless-stopped nginx:alpine
docker run -d --name redis --restart unless-stopped redis:alpine
docker ps
```

---

## Step 3 — 사전 준비

```bash
ln -sf ~/AiSecurity/venv ~/AiSecurity/.venv
sudo chown $USER:$USER ~/falco_raw.log ~/attack_windows.txt 2>/dev/null || true
> ~/falco_raw.log
> ~/attack_windows.txt
rm -f ~/events.csv ~/labeled.csv
```

---

## Step 4 — Falco 시작

```bash
sudo falco \
    -o engine.kind=modern_ebpf \
    -o json_output=true \
    -o file_output.enabled=true \
    -o file_output.filename=/home/$USER/falco_raw.log \
    -o file_output.keep_alive=false \
    2>/dev/null &

sleep 5

# 동작 확인 (1 이상이면 정상)
docker exec nginx sh -c "cat /etc/shadow" 2>/dev/null
sleep 3
grep -c '{' ~/falco_raw.log
```

---

## Step 5 — 수집 루프 실행 (~8시간)

```bash
cd ~/AiSecurity && git pull

nohup bash ~/AiSecurity/data_collection/collect_loop.sh 20 \
    >> ~/collect.log 2>&1 &

tail -f ~/collect.log
```

> `Ctrl+C`로 tail을 종료해도 수집은 백그라운드에서 계속 됩니다.

---

## Step 6 — 완료 확인

```bash
wc -l ~/labeled.csv          # 500줄 이상이면 OK
cat ~/attack_windows.txt     # 20개 윈도우 확인
```

---

## Step 7 — 로컬로 파일 복사 (Windows PowerShell)

```powershell
scp -P 2222 user32211690@127.0.0.1:~/labeled.csv E:\dhapr\Downloads\AiSecurity\data\labeled.csv
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `grep -c '{' falco_raw.log` = 0 | stdout 버퍼링 | Step 4의 `file_output` 방식 사용 |
| `falco_raw.log: 허가 거부` | sudo가 root 소유로 생성 | `sudo chown $USER:$USER ~/falco_raw.log` |
| `collect_loop.sh: 그런 파일 없음` | venv 이름 불일치 | Step 3의 `ln -sf` 실행 |
| Falco `Killed` | 메모리 부족 (EC2 t3.micro) | VM에서만 실행 |
