---
level: L3
protection: 자유롭게 수정 가능
---

# L3 Progress — 현재 진행 상황

> 주간 업무, 진행 상황, 다음 단계를 기록한다.
> 자유롭게 수정 가능. 세션 종료 시 /handoff로 업데이트.

---

## 현재 브랜치
`feature/data-collection` (preprocessing 진행 중)

---

## 완료 항목

- [x] `feature/data-collection`: `falco_to_csv.py`, `auto_labeling.py`, `normal_traffic_docker.sh`, `attack_simulator_docker.sh`, `collect_loop.sh`
- [x] `fix/ec2-setup-clone-branch`: `ec2_setup.sh` 수정 (브랜치명, Falco file_output, sg 제거, watchdog)
- [x] VirtualBox Ubuntu 26.04 VM 신규 설치 — Docker, Falco Modern eBPF, nginx/redis 컨테이너 세팅 완료
- [x] **데이터 수집 완료** — 8라운드 collect_loop.sh 실행 (VM 종료로 중단), labeled.csv 생성 → `data/labeled.csv` 로컬 확보
- [x] `scripts/falco_watchdog.sh` 추가 — Falco 크래시 시 자동 재시작
- [x] `preprocessing/preprocess.py` 작성 — 단일 스크립트로 전처리 전 단계 처리

---

## 데이터 현황

| 항목 | 값 |
|------|-----|
| VM | VirtualBox Ubuntu 26.04 |
| Falco | Modern eBPF 0.44.0, watchdog으로 자동 재시작 |
| 실행 컨테이너 | nginx:alpine, redis:alpine |
| 총 이벤트 | 214,962개 |
| label=1 (공격) | 95,588개 (44.5%) |
| label=0 (정상) | 119,374개 (55.5%) |
| 공격 윈도우 수 | 8개 |
| labeled.csv 위치 | `data/labeled.csv` ✅ |

**label 균형 양호 (55:45)** — `class_weight='balanced'` 선택사항 (불필요할 수도 있음, 윈도우 집계 후 재확인)

---

## VM 트러블슈팅 기록

| 증상 | 원인 | 해결 |
|------|------|------|
| `falco_raw.log` 이벤트 0개 | stdout 버퍼링 | `file_output` 방식으로 전환 |
| Falco 공격 중 크래시 | 대량 syscall 처리 중 종료 (원인 미상) | `falco_watchdog.sh`로 자동 재시작 |
| watchdog이 `/root/falco_raw.log`에 기록 | sudo 실행 시 `$HOME=/root` | `SUDO_USER`로 실제 홈 경로 조회 |
| `sg: command not found` | sg 미설치 환경 | 제거 후 재접속 안내로 대체 |

---

## 다음 단계

### Step 1: 전처리 실행 (VM 또는 로컬)

```bash
# VM에서 (패키지 설치 후)
.venv/bin/pip install -r requirements.txt
.venv/bin/python preprocessing/preprocess.py \
    --input ~/labeled.csv \
    --output-dir ~/data
```

**입력:** `data/labeled.csv`
**출력:** `data/X_train.npy`, `data/X_test.npy`, `data/y_train.npy`, `data/y_test.npy`, `data/scaler.pkl`, `data/encoders.pkl`

> `stratify=None` — sklearn은 `shuffle=False`와 `stratify` 동시 사용 불가.
> 시계열 순서 보존(`shuffle=False`)이 우선이므로 stratify 포기.

### Step 2: npy 로컬 복사 후 모델 학습 브랜치
```powershell
scp -P 2222 user32211690@127.0.0.1:~/data/*.npy E:\dhapr\Downloads\AiSecurity\data\
scp -P 2222 user32211690@127.0.0.1:~/data/*.pkl E:\dhapr\Downloads\AiSecurity\data\
```

---

## 미결 사항

- `preprocess.py` VM에서 실행 미완료 (패키지 설치 후 실행 필요)
- npy 파일 로컬 복사 미완료
- minikube, helm 미설치 (서비스 배포 단계에서 도입 예정 — 현재 수집/학습에는 불필요)

---

## 필수 설치 상태

| 도구 | 상태 |
|------|------|
| minikube | ❌ 미설치 |
| helm | ❌ 미설치 |
| kubectl | ✅ 완료 |
| docker | ✅ 완료 (VM) |
| falco | ✅ 완료 (VM, watchdog 포함) |
