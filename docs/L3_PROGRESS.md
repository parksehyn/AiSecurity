---
level: L3
protection: 자유롭게 수정 가능
---

# L3 Progress — 현재 진행 상황

> 주간 업무, 진행 상황, 다음 단계를 기록한다.
> 자유롭게 수정 가능. 세션 종료 시 /handoff로 업데이트.

---

## 현재 브랜치
`feature/data-collection` (코드 완료, PR 미생성 → main 미머지)

---

## 완료 항목

- [x] `feature/data-collection`: `falco_to_csv.py`, `auto_labeling.py`, `normal_traffic_docker.sh`, `attack_simulator_docker.sh`
- [x] VirtualBox Ubuntu VM — Falco Modern eBPF 설치, Docker syscall 수집 확인
- [x] `~/falco_raw.log` → `~/events.csv` → `~/labeled.csv` 파이프라인 동작 확인

---

## 데이터 환경 (VM)

| 항목 | 값 |
|------|-----|
| VM | VirtualBox Ubuntu |
| Falco | Modern eBPF (`falco-modern-bpf.service`) |
| 실행 컨테이너 | nginx, redis |
| 데이터 파일 | `~/events.csv`, `~/labeled.csv` (VM 홈) |
| 현재 데이터 수 | 31개 (부족) |

**데이터 부족 해결:** VM에서 `attack_simulator_docker.sh` 반복 실행 후 재수집

---

## 다음 단계

### Step 1: data-collection PR 머지
```bash
# PR 생성 후 main 머지
feat: data collection pipeline (#이슈번호)
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

**입력:** `labeled.csv`
**출력:** `X_train.npy`, `X_test.npy`, `y_train.npy`, `y_test.npy`

---

## 미결 사항

- 데이터 부족(31개) → 최소 500개 이상 수집 후 preprocessing 진행 권장
- minikube, helm 미설치 (현재 VM Docker 환경으로 대체 중)

---

## 필수 설치 상태

| 도구 | 상태 |
|------|------|
| minikube | ❌ 미설치 |
| helm | ❌ 미설치 |
| kubectl | ✅ 완료 |
| docker | ✅ 완료 |
