# Kubernetes 런타임 이상 탐지 시스템

> AI 기반 컨테이너 보안 — Falco syscall 분석을 통한 실시간 공격 탐지

---

## 프로젝트 개요

Kubernetes 환경에서 컨테이너의 syscall 이벤트를 Falco로 수집하고, Random Forest / LSTM 모델로 학습하여 실시간으로 공격을 탐지하는 시스템입니다.

### 탐지 대상 공격 (MITRE ATT&CK for Containers)

| # | 시나리오 | MITRE ID |
|---|----------|----------|
| 1 | 컨테이너 내 쉘 실행 | T1609 |
| 2 | 민감 파일 탐색 | T1552 |
| 3 | 네트워크 스캔 | T1046 |
| 4 | 권한 상승 시도 | T1611 |

### 기술 스택

```
수집     : Falco Modern eBPF 0.44.0, VirtualBox Ubuntu VM
ML       : Python 3.11, scikit-learn, TensorFlow/Keras
서비스   : FastAPI, Streamlit, uvicorn
```

---

## 시스템 아키텍처

```
┌─── VirtualBox VM ──────────────────────────┐
│  [nginx]  [redis]  [webapp]                │
│      ↓ syscall 이벤트                      │
│  [Falco Modern eBPF]                       │
│      ↓ JSON 로그                           │
│  [falco_to_csv.py → labeled.csv]           │
└────────────────────────────────────────────┘
                    ↓
┌─── ML 파이프라인 ──────────────────────────┐
│  preprocess.py → 30초 윈도우 집계 (397개) │
│  train_rf.py   → rf_model.pkl              │
│  train_lstm.py → lstm_model.keras          │
└────────────────────────────────────────────┘
                    ↓
┌─── 서비스 ─────────────────────────────────┐
│  FastAPI (/detect, /health)                │
│  Streamlit 대시보드 (실시간 탐지 시각화)   │
└────────────────────────────────────────────┘
```

### 디렉토리 구조

```
k8s-anomaly-detection/
├── data_collection/
│   ├── falco_to_csv.py
│   ├── auto_labeling.py
│   ├── normal_traffic_docker.sh
│   ├── attack_simulator_docker.sh
│   └── collect_loop.sh
├── preprocessing/
│   └── preprocess.py
├── models/
│   ├── train_rf.py
│   ├── train_lstm.py
│   ├── compare_models.py
│   └── saved/
│       ├── rf_model.pkl
│       ├── lstm_model.keras
│       └── scaler.pkl
├── service/
│   ├── api/
│   │   ├── main.py
│   │   ├── inference.py
│   │   └── alert.py
│   └── dashboard/
│       └── app.py
└── docs/
    ├── L1_FOUNDATION.md
    ├── L2_ARCHITECTURE.md
    └── L3_PROGRESS.md
```

---

## 데이터셋

| 항목 | 값 |
|------|-----|
| 총 이벤트 | 214,962개 |
| 수집 시간 | 약 3.3시간 |
| 총 윈도우 (30초) | 397개 |
| 정상 윈도우 (label=0) | 278개 (70%) |
| 공격 윈도우 (label=1) | 119개 (30%) |
| Train / Test | 317 / 80 (8:2) |

### 입력 피처 (5개)

| 피처 | 설명 |
|------|------|
| `event_count` | 30초 내 syscall 총 수 (활동의 양) |
| `unique_syscalls` | 고유 syscall 종류 수 (행위의 다양성) |
| `unique_processes` | 고유 프로세스 수 (실행의 흔적) |
| `critical_count` | Falco CRITICAL 이벤트 수 (기존 보안 룰 점수) |
| `sensitive_access` | 민감 파일 접근 횟수 (최종 공격 의도) |

---

## 모델 성능

### Random Forest vs LSTM 비교

| Metric | RF | LSTM | 목표 |
|--------|-----|------|------|
| Precision | **0.9500** ✓ | 0.8750 ✗ | ≥ 0.90 |
| Recall | **0.9500** ✓ | 0.9333 ✗ | ≥ 0.95 |
| F1 | **0.9500** ✓ | 0.9032 ✓ | ≥ 0.90 |
| FPR | **0.0167** ✓ | 0.0571 ✗ | ≤ 0.05 |
| AUC | **0.9958** ✓ | 0.9924 ✓ | ≥ 0.95 |
| **달성** | **5/5** | 2/5 | |

> RF가 이 데이터셋에서 명확히 우세. 이론상 LSTM이 스텔스 공격에 유리하나, 즉각적 공격 패턴 + 데이터 부족(test 50개)으로 RF 우세.

---

## 실행 방법 (How to Run)

### 사전 요구사항

```bash
pip install fastapi uvicorn scikit-learn joblib numpy streamlit pandas requests
```

### 1. 데이터 수집 (VM에서)

```bash
# 정상 트래픽 생성
bash data_collection/normal_traffic_docker.sh

# 공격 시뮬레이션
bash data_collection/attack_simulator_docker.sh

# Falco 로그 → CSV 변환
python data_collection/falco_to_csv.py --input falco_raw.log --output events.csv

# 레이블 부여
python data_collection/auto_labeling.py \
    --input events.csv --output labeled.csv \
    --attack-windows "2025-04-26 16:00:00,2025-04-26 16:30:00"
```

### 2. 전처리

```bash
python preprocessing/preprocess.py \
    --input data/labeled.csv \
    --output-dir data/
```

### 3. 모델 학습

```bash
# Random Forest (로컬)
python models/train_rf.py --data-dir data/

# LSTM (Google Colab 권장 — GPU 필요)
# Colab에 X_train.npy, X_test.npy, y_train.npy, y_test.npy, scaler.pkl 업로드 후 실행
python models/train_lstm.py --data-dir data/
```

### 4. 모델 비교

```bash
python models/compare_models.py --data-dir data/
```

### 5. FastAPI 서버 실행

```bash
uvicorn service.api.main:app --reload
# http://127.0.0.1:8000/docs 에서 API 문서 확인
```

### 6. Streamlit 대시보드 실행

```bash
# FastAPI 서버가 실행 중인 상태에서
streamlit run service/dashboard/app.py
# http://localhost:8501
```

### API 사용 예시

```bash
curl -X POST http://127.0.0.1:8000/detect \
  -H "Content-Type: application/json" \
  -d '{
    "container_name": "nginx",
    "event_count": 300,
    "unique_syscalls": 25,
    "unique_processes": 8,
    "critical_count": 5,
    "sensitive_access": 6
  }'
```

응답:
```json
{
  "status": "ALERT",
  "container": "nginx",
  "confidence": 0.985,
  "action": "pod isolation recommended",
  "timestamp": "2026-05-30T06:00:00+00:00"
}
```

---

## AI 도구 활용 전략 (Prompting Log)

### 하네스 기법 + 서브 에이전트 구조

부모 Claude가 전체 코드를 작성/수정하고, 서브 에이전트는 검증/분석 역할만 담당.

```
[부모 Claude (디렉터)]
        ↓ 지시
┌───────┼───────────┬──────────┐
↓       ↓           ↓          ↓
qa-  code-      doc-       architect
validator reviewer  guardian
검증   버그탐지  문서모순   설계분석
```

### 서브 에이전트 활용 결과

| 에이전트 | 호출 시점 | 발견/기여 | 결과 |
|----------|-----------|-----------|------|
| `qa-validator` | 전처리 완료 후 | 윈도우 분포 검증, 레이블 비율 확인 | 데이터 편향 사전 확인 |
| `code-reviewer` | train_rf.py 작성 후 | pickle → joblib 권장 | joblib으로 수정 |
| `code-reviewer` | service/api/ 작성 후 | thread-safety 문제, 에러 핸들링 누락 | lifespan 전환, 503 처리 추가 |
| `doc-guardian` | 중간 체크 | L3 진행 상황 4단계 차이 | L3_PROGRESS.md 업데이트 |
| `doc-guardian` | 최종 체크 | `lstm_model.h5` vs `.keras` 불일치 | 런타임 오류 사전 방지 |
| `architect` | 프로젝트 완료 후 | 향후 개선 방향 10개 도출 | 단기/중기/장기 로드맵 수립 |

### Git 협업 전략

- **브랜치 전략**: feature 브랜치 → PR → main 머지
- **총 PR**: 5개 (`data-collection`, `train-rf`, `train-lstm`, `service-api`, `dashboard`)
- 각 PR마다 `code-reviewer` 서브 에이전트로 자동 검증

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `falco_raw.log` 이벤트 0개 | stdout 버퍼링 | `file_output` 방식으로 전환 |
| Falco 공격 중 크래시 | 대량 syscall 처리 중 종료 | `falco_watchdog.sh`로 자동 재시작 |
| watchdog이 `/root/falco_raw.log`에 기록 | sudo 실행 시 `$HOME=/root` | `SUDO_USER`로 실제 홈 경로 조회 |
| `sg: command not found` | sg 미설치 환경 | 제거 후 재접속 안내로 대체 |
| VM 디스크 풀 (DrvVD_DISKFULL) | tensorflow 설치 중 캐시 누적 | `pip cache purge` 후 재설치 |
| tensorflow 설치 불필요 | LSTM 학습을 Colab에서 진행 | VM에서 tensorflow 제거, Colab T4 GPU 활용 |
| sklearn 버전 불일치 경고 | VM(1.8.0) vs Colab(1.6.1) | 결과에 영향 없음, 경고 무시 |
| FastAPI lazy init thread-safety | 동시 요청 시 레이스 컨디션 가능 | `lifespan` 이벤트로 서버 시작 시 1회 로드 |
| 정상 트래픽 ALERT 오탐 | 윈도우 397개 부족, RF 결정 경계 불안정 | 데이터 추가 수집으로 해결 가능 |

---

## 한계 및 향후 개선 방향

### 현재 한계

- 윈도우 397개 부족 → RF 결정 경계 불안정, 오탐 발생
- LSTM test 시퀀스 50개 → 통계 불안정
- 공격 시뮬레이션 4개 패턴만 커버 (실제 공격 다양성 미반영)
- 피처 일부가 Falco 룰 기반 집계값 (raw syscall 피처로 교체 필요)

### 향후 개선 방향

| 단계 | 항목 |
|------|------|
| 단기 | RF `min_samples_leaf` 튜닝, `avg_interval` 피처 추가 |
| 중기 | 데이터 2,000+ 윈도우 확보, LSTM 컨테이너별 시퀀스 분리, T1070/T1496 공격 추가 |
| 장기 | minikube 실 배포, SHAP 설명 추가, 온라인 학습 파이프라인 |
