# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Kubernetes Runtime Anomaly Detection System

syscall 분석 기반 컨테이너 런타임 이상 탐지 시스템. Falco로 수집 → RF/LSTM 학습 → FastAPI + Streamlit 제공.

**Tech Stack:** minikube, Falco, Helm / Python 3.11, scikit-learn, TensorFlow, pandas / FastAPI, Streamlit

## ⚠️ 개발 시작 전 필수 설치

| 도구 | 설치 명령 | 상태 |
|------|-----------|------|
| minikube | `winget install Kubernetes.minikube` | 미설치 |
| helm | `winget install Helm.Helm` | 미설치 |
| kubectl | `winget install Kubernetes.kubectl` | 완료 |
| docker | Docker Desktop | 완료 |

설치 후 진행 순서: `minikube start` → Falco(helm) → pod 배포 → `normal_traffic.sh` → `attack_simulator.sh` → `falco_to_csv.py` → `auto_labeling.py`

## Commands

```bash
# 테스트 전체 실행
pytest data_collection/

# 단일 테스트 파일
pytest data_collection/test_data_collection.py -v

# 단일 테스트 케이스
pytest data_collection/test_data_collection.py::TestParseEvent::test_valid_event -v

# Falco 로그 → CSV
python data_collection/falco_to_csv.py --input falco.log --output events.csv
# 또는 실시간 pipe
sudo falco -o json_output=true | python data_collection/falco_to_csv.py --output events.csv

# 자동 레이블링
python data_collection/auto_labeling.py \
    --input events.csv --output labeled.csv \
    --attack-windows "2025-04-26 16:00:00,2025-04-26 16:30:00"
```

## 파이프라인 데이터 흐름

```
Falco JSON → falco_to_csv.py → events.csv → auto_labeling.py → labeled.csv
                                                                      ↓
                                              preprocessing/ (label_encoding → sliding_window → feature_engineering → split)
                                                                      ↓
                                              models/ (train_rf.py / train_lstm.py → evaluate.py → compare_models.py)
                                                                      ↓
                                              service/ (FastAPI inference + Streamlit dashboard)
```

**`falco_to_csv.py` 출력 스키마** (7개 컬럼, 하위 모든 단계의 입력):

| 컬럼 | Falco 소스 | 비고 |
|------|-----------|------|
| `timestamp` | `event.time` | ISO 8601 |
| `priority` | `event.priority` | CRITICAL/WARNING/INFO |
| `rule` | `event.rule` | Falco rule 이름 |
| `syscall` | `output_fields.evt.type` | 범주형 → LabelEncoding 대상 |
| `proc_name` | `output_fields.proc.name` | 범주형 → LabelEncoding 대상 |
| `container_name` | `output_fields.container.name` | 범주형 → LabelEncoding 대상 |
| `fd_name` | `output_fields.fd.name` | 민감 파일 탐지용 |

`auto_labeling.py`가 `label` 컬럼(0/1)을 추가해 `labeled.csv` 생성.

## Git Workflow

`feature/<name>` 브랜치에서 개발 → 테스트 통과 → PR → `main` 머지. `main` 직접 커밋 금지.

브랜치 계획: `feature/data-collection` → `feature/preprocessing` → `feature/train-rf` → `feature/train-lstm` → `feature/api` → `feature/dashboard`

## 환경변수 & GitHub API

시크릿은 `.env`로 관리 (`.gitignore` 포함, 커밋 금지). `.env.example`만 커밋.

GitHub API는 반드시 `scripts/gh_api.ps1`의 `Invoke-GhApi`를 사용한다. PowerShell 5.1 기본 인코딩(UTF-16)으로 인해 한글이 깨지므로, 직접 `Invoke-RestMethod`를 쓰지 말 것 — 헬퍼가 UTF-8 변환을 처리함.

## 이슈 & PR 형식

**이슈:** 개요 / 작업 범위(체크리스트) / 완료 기준 / 참고(브랜치명)

**PR:** 개요 + `Closes #n` / 변경 사항 / 테스트 결과 / 미완료(추후)

PR 제목: `feat: <기능명> (#<이슈번호>)`

## How Claude Should Work

- 불확실하면 가정하지 말고 먼저 물어본다
- 요청한 것만 구현한다 — 추측성 기능, 불필요한 추상화 금지
- 기존 코드는 요청과 직접 관련된 줄만 수정한다
- 멀티스텝 작업은 계획을 먼저 제시하고 각 단계를 검증한다

## Coding Rules

- `random_state=42` 고정
- 스케일러: `fit_transform`은 train에만, test는 `transform`만
- `shuffle=False` — 시계열 데이터 셔플 금지 (데이터 누수 발생)
- 공격 시뮬레이션은 minikube 내부에서만 실행
- `data/`, `models/saved/`는 `.gitignore`에 포함 — 원시 데이터/모델 커밋 금지

## 현재 진행 상황 & 다음 단계

### 완료
- `feature/data-collection` 브랜치: `falco_to_csv.py`, `auto_labeling.py`, `normal_traffic_docker.sh`, `attack_simulator_docker.sh` 구현 완료
- VirtualBox Ubuntu VM에 Falco Modern eBPF 설치 → Docker 컨테이너 syscall 수집 확인
- `~/falco_raw.log` → `~/events.csv` → `~/labeled.csv` 파이프라인 동작 확인

### 데이터 환경 (VM)
- VM: VirtualBox Ubuntu, Falco Modern eBPF (`falco-modern-bpf.service`)
- 컨테이너: `docker ps` → nginx, redis 실행 중
- 데이터 파일: `~/events.csv`, `~/labeled.csv` (VM 홈 디렉토리)
- 데이터 부족 (31개) → VM에서 `attack_simulator_docker.sh` 반복 실행 후 재수집 필요

### 다음 단계: `feature/preprocessing` 브랜치

```
1. git checkout -b feature/preprocessing
2. preprocessing/label_encoding.py   — syscall, proc_name, container_name LabelEncoding
3. preprocessing/sliding_window.py   — 30초 윈도우 집계
4. preprocessing/feature_engineering.py — 5개 통계 피처 추출
5. preprocessing/train_test_split.py — 8:2, shuffle=False, stratify=y
```

입력: `labeled.csv` / 출력: `X_train.npy`, `X_test.npy`, `y_train.npy`, `y_test.npy`

## 핵심 설계 결정

**레이블 혼동 주의:** ground truth label(0=정상, 1=공격)과 LabelEncoding(범주형 피처 인코딩)은 완전히 별개의 단계다.

**모델 전략:** RF(1 window 스냅샷, 빠른 탐지)와 LSTM(30 window 시퀀스, 은닉 공격)을 별도 학습 후 비교. 앙상블 금지.

**평가 우선순위:** Recall ≥ 0.95 최우선 — 공격 미탐지는 실제 침해로 이어진다.

**⚠️ auto_labeling 한계 — 호스트 이벤트 오염:**

시간 기반 레이블링은 이벤트 내용을 보지 않고 timestamp만 본다. 따라서 공격 윈도우 밖이라도 호스트 OS의 정상 동작(예: `update-notifier` → `pkexec` → `/etc/pam.d/*` 접근)이 label=0으로 잘못 분류될 수 있다.

전처리 단계에서 반드시 호스트 이벤트를 필터링한다:

```python
# container_name이 'host'인 이벤트 제외 — 호스트 OS 이벤트는 학습 대상이 아님
df = df[df["container_name"] != "host"]
```
