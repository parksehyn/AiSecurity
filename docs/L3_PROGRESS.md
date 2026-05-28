---
level: L3
protection: 자유롭게 수정 가능
---

# L3 Progress — 현재 진행 상황

> 주간 업무, 진행 상황, 다음 단계를 기록한다.
> 자유롭게 수정 가능. 세션 종료 시 /handoff로 업데이트.

---

## 현재 브랜치
`main` (data-collection PR #4 머지 완료)

---

## 완료 항목

- [x] `feature/data-collection`: `falco_to_csv.py`, `auto_labeling.py`, `normal_traffic_docker.sh`, `attack_simulator_docker.sh`, `collect_loop.sh` — PR #4 main 머지 완료
- [x] `fix/ec2-setup-clone-branch`: `ec2_setup.sh` 수정 (브랜치명, Falco file_output, sg 제거, watchdog) — main 머지 완료
- [x] VirtualBox Ubuntu 26.04 VM 신규 설치 — Docker, Falco Modern eBPF, nginx/redis 컨테이너 세팅 완료
- [x] **데이터 수집 완료** — 20라운드 collect_loop.sh 실행, labeled.csv 생성
- [x] `scripts/falco_watchdog.sh` 추가 — Falco 크래시 시 자동 재시작

---

## 데이터 현황

| 항목 | 값 |
|------|-----|
| VM | VirtualBox Ubuntu 26.04 |
| Falco | Modern eBPF 0.44.0, watchdog으로 자동 재시작 |
| 실행 컨테이너 | nginx:alpine, redis:alpine |
| 총 이벤트 | 712개 |
| label=1 (공격) | 633개 (89%) |
| label=0 (정상) | 79개 (11%) |
| 공격 윈도우 수 | 39개 |
| labeled.csv 위치 | VM `~/labeled.csv` → Windows `data/labeled.csv` (scp 대기 중) |

**주의: label 불균형 심함 (89:11)** → preprocessing/training 단계에서 `class_weight='balanced'` 또는 언더샘플링 필요

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

### Step 1: labeled.csv Windows로 복사
```powershell
# Windows PowerShell에서
mkdir C:\Users\dhapr\AiSecurity\data -Force
scp -P 2222 user32211690@127.0.0.1:~/labeled.csv C:\Users\dhapr\AiSecurity\data\labeled.csv
```

### Step 2: `feature/preprocessing` 브랜치
```bash
git checkout -b feature/preprocessing
```

| 순서 | 파일 | 역할 |
|------|------|------|
| 1 | `preprocessing/filter.py` | container_name == 'host' 제거 |
| 2 | `preprocessing/label_encoding.py` | syscall, proc_name, container_name LabelEncoding |
| 3 | `preprocessing/sliding_window.py` | 30초 윈도우 집계 |
| 4 | `preprocessing/feature_engineering.py` | 5개 통계 피처 추출 |
| 5 | `preprocessing/train_test_split.py` | 8:2, shuffle=False, stratify=y |

**입력:** `data/labeled.csv`
**출력:** `data/X_train.npy`, `data/X_test.npy`, `data/y_train.npy`, `data/y_test.npy`

---

## 미결 사항

- labeled.csv Windows 복사 미완료 (scp 대기 중)
- label 불균형 (89:11) — preprocessing 단계에서 처리 필요
- minikube, helm 미설치 (현재 VM Docker 환경으로 대체 중)

---

## 필수 설치 상태

| 도구 | 상태 |
|------|------|
| minikube | ❌ 미설치 |
| helm | ❌ 미설치 |
| kubectl | ✅ 완료 |
| docker | ✅ 완료 (VM) |
| falco | ✅ 완료 (VM, watchdog 포함) |
