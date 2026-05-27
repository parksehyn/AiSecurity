---
level: L2
protection: 수정 시 L3 전부 재검토 강제 (doc-guardian 실행)
---

# L2 Architecture — 바뀌면 골치아픈 설계

> 도메인 모델, 파이프라인 구조, 스키마, 설계 결정을 정의한다.
> 이 문서가 바뀌면 L3(진행 상황, 코드 계획)에 파급 효과가 생긴다.
> 수정 후 반드시 doc-guardian으로 파급 체크를 실행한다.

---

## Tech Stack

| 레이어 | 기술 |
|--------|------|
| 데이터 수집 | minikube, Falco, Helm |
| 처리·학습 | Python 3.11, scikit-learn, TensorFlow, pandas |
| 서비스 | FastAPI, Streamlit |

---

## 파이프라인 데이터 흐름

```
Falco JSON
    ↓ falco_to_csv.py
events.csv  (7컬럼 스키마)
    ↓ auto_labeling.py
labeled.csv (8컬럼: +label)
    ↓ preprocessing/
    │   filter.py               container_name == 'host' 제거 (최초 단계)
    │   label_encoding.py       범주형 3개 컬럼 인코딩
    │   sliding_window.py       30초 윈도우 집계
    │   feature_engineering.py  5개 통계 피처 추출
    │   train_test_split.py     8:2, shuffle=False
    ↓
X_train.npy / X_test.npy / y_train.npy / y_test.npy
    ↓ models/
    │   train_rf.py             RF (1 window 스냅샷)
    │   train_lstm.py           LSTM (30 window 시퀀스)
    │   evaluate.py             Recall/Precision/F1/FPR/AUC
    │   compare_models.py       RF vs LSTM 비교
    ↓
service/
    FastAPI inference + Streamlit dashboard
```

---

## falco_to_csv.py 출력 스키마 (하위 모든 단계의 입력)

> ⚠️ 이 스키마가 바뀌면 auto_labeling, preprocessing 전부 수정 필요

| 컬럼 | Falco 소스 | 타입 | 비고 |
|------|-----------|------|------|
| `timestamp` | `event.time` | str (ISO 8601) | |
| `priority` | `event.priority` | str | CRITICAL/WARNING/INFO |
| `rule` | `event.rule` | str | Falco rule 이름 |
| `syscall` | `output_fields.evt.type` | str | 범주형 → LabelEncoding 대상 |
| `proc_name` | `output_fields.proc.name` | str | 범주형 → LabelEncoding 대상 |
| `container_name` | `output_fields.container.name` | str | 범주형 → LabelEncoding 대상 |
| `fd_name` | `output_fields.fd.name` | str | 민감 파일 탐지용 |

`auto_labeling.py`가 `label` 컬럼(int: 0=정상, 1=공격)을 추가 → `labeled.csv`

---

## 모델 전략

| 모델 | 입력 | 탐지 대상 | 특성 |
|------|------|-----------|------|
| RF | 1 window 스냅샷 | 즉각적 이상 | 빠른 탐지, 해석 가능 |
| LSTM | 30 window 시퀀스 | 은닉·지속 공격 | 시계열 패턴 학습 |

**앙상블 금지** — 별도 학습 후 성능 비교가 목적

**평가 기준 (전부 충족 필요):**

| 지표 | 기준 | 비고 |
|------|------|------|
| Recall | ≥ 0.95 | 최우선 — 공격 미탐지 방지 |
| Precision | ≥ 0.90 | |
| F1 | ≥ 0.90 | |
| FPR (False Positive Rate) | ≤ 0.05 | 오탐 허용 범위 |
| AUC-ROC | ≥ 0.95 | 전체 분류 성능 |

---

## 핵심 설계 결정

### 레이블 혼동 주의
`label`(ground truth: 0/1)과 LabelEncoding(범주형 피처 인코딩)은 완전히 별개.
LabelEncoder를 `label` 컬럼에 적용하지 않는다.

### 호스트 이벤트 오염
시간 기반 레이블링은 timestamp만 보므로, 공격 윈도우 밖 호스트 OS 정상 동작이 label=0으로 잘못 분류될 수 있다.
전처리 최초 단계에서 반드시 필터링:
```python
df = df[df["container_name"] != "host"]
```

### 슬라이딩 윈도우
30초 윈도우로 집계. LSTM은 30개 윈도우를 시퀀스로 입력 → **30초 × 30개 = 15분 시퀀스**.
윈도우 크기 변경 시 파급: `sliding_window.py` → `train_lstm.py` input shape → `service/` inference shape 전부 수정 필요.

---

## 브랜치 계획

```
feature/data-collection  ✅ 코드 완료 (데이터 수집 진행 중, main 미머지)
feature/preprocessing    ← 다음 (data-collection 머지 후 시작)
feature/train-rf
feature/train-lstm
feature/api
feature/dashboard
```

---

## 환경변수 & GitHub API

- 시크릿: `.env` 관리 (`.gitignore` 포함). `.env.example`만 커밋
- GitHub API: 반드시 `scripts/gh_api.ps1`의 `Invoke-GhApi` 사용
  (PowerShell 5.1 UTF-16 한글 깨짐 → 헬퍼가 UTF-8 변환 처리)
