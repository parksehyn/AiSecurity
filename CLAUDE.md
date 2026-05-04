# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Kubernetes Runtime Anomaly Detection System

AI-based container security system that detects attacks in real-time using syscall analysis.

## Git Workflow

- 기능 단위로 브랜치를 생성해 개발한다: `git checkout -b feature/<name>`
- 브랜치에서 개발 → 테스트 통과 확인 → PR 생성 순서를 따른다
- PR은 테스트가 완수된 이후에만 요청한다
- `main` 브랜치에 직접 커밋하지 않는다

```
main
 └── feature/data-collection
 └── feature/preprocessing
 └── feature/train-rf
 └── feature/train-lstm
 └── feature/api
 └── feature/dashboard
```

## 환경변수 관리

시크릿(토큰, API 키)은 `.env` 파일로 관리한다. `.env`는 `.gitignore`에 포함되어 커밋되지 않는다.

```bash
# 최초 설정
cp .env.example .env
# .env 파일에 실제 값 입력
```

```
# .env
GITHUB_TOKEN=ghp_...
GITHUB_REPO=parksehyn/AiSecurity
```

GitHub API 호출은 `scripts/gh_api.ps1`의 `Invoke-GhApi` 헬퍼를 사용한다:

```powershell
. .\scripts\gh_api.ps1

Invoke-GhApi -Method Post -Endpoint "/issues" -Body @{
    title = "feat: 새 기능"
    body  = "..."
}
```

- `.env.example`은 커밋 대상 — 키 이름만 적고 값은 비워둔다
- `.env`는 로컬 전용 — 절대 커밋하지 않는다
- 토큰을 채팅/코드에 직접 노출했다면 즉시 폐기 후 재발급한다
- PowerShell 5.1은 기본 인코딩이 UTF-16이므로 API body는 반드시 UTF-8 바이트로 변환해 전송한다 (`gh_api.ps1`이 이를 처리함 — 직접 `Invoke-RestMethod`를 쓰지 말 것)

## 이슈 & PR 형식

이슈와 PR은 아래 형식을 통일해서 사용한다. 모두 `Invoke-GhApi`로 생성하며 한글이 깨지지 않는다.

**이슈 형식**

```
## 개요
[한 줄 설명]

## 작업 범위
- [ ] 항목 1
- [ ] 항목 2

## 완료 기준
- 조건 1
- 조건 2

## 참고
- 관련 브랜치: `feature/<name>`
```

**PR 형식**

```
## 개요
[한 줄 설명]

Closes #<이슈번호>

## 변경 사항
- `파일명` — 설명

## 테스트 결과
[통과한 테스트 수 / 명령어 출력]

## 미완료 (추후)
- [인프라 의존 등 defer 항목]
```

- PR 제목은 `feat: <기능명> (#<이슈번호>)` 형식을 따른다
- PR은 반드시 연결된 이슈 번호를 `Closes #n`으로 명시한다

## How Claude Should Work

### 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: *"Would a senior engineer say this is overcomplicated?"* If yes, simplify.

### 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: **Every changed line should trace directly to the user's request.**

### 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Project Summary

Collect syscall logs from Kubernetes containers via Falco, train Random Forest and LSTM models separately for comparison, and serve real-time detection through FastAPI + Streamlit dashboard.

## Tech Stack

```
Infrastructure : minikube, Falco, Docker, Helm
Data / ML      : Python 3.11, pandas, numpy, scikit-learn, TensorFlow/Keras, imbalanced-learn
Service        : FastAPI, Streamlit, uvicorn
```

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Data pipeline (run in order)
python data_collection/falco_to_csv.py
python data_collection/auto_labeling.py
python preprocessing/label_encoding.py
python preprocessing/sliding_window.py
python preprocessing/feature_engineering.py
python preprocessing/train_test_split.py

# Train models
python models/train_rf.py
python models/train_lstm.py

# Evaluate and compare
python models/evaluate.py
python models/compare_models.py

# Run API server
uvicorn service.api.main:app --reload --port 8000

# Run dashboard
streamlit run service/dashboard/app.py

# Data collection (inside minikube only)
bash data_collection/normal_traffic.sh
bash data_collection/attack_simulator.sh
```

## Directory Structure

```
k8s-anomaly-detection/
├── data_collection/
│   ├── normal_traffic.sh        # Auto-generate normal workload traffic
│   ├── attack_simulator.sh      # Run 4 MITRE ATT&CK attack scenarios
│   ├── falco_to_csv.py          # Convert Falco JSON logs → CSV
│   └── auto_labeling.py         # Time-based automatic label assignment
│
├── preprocessing/
│   ├── label_encoding.py        # Encode categorical features to integers
│   ├── sliding_window.py        # 30s window aggregation
│   ├── feature_engineering.py   # Extract 5 statistical features per window
│   └── train_test_split.py      # 8:2 split with stratify + time ordering
│
├── models/
│   ├── train_rf.py              # Train Random Forest (baseline)
│   ├── train_lstm.py            # Train LSTM (sequential)
│   ├── evaluate.py              # Compute 5 evaluation metrics
│   ├── compare_models.py        # Side-by-side model comparison
│   └── saved/
│       ├── rf_model.pkl
│       ├── lstm_model.h5
│       └── scaler.pkl
│
├── service/
│   ├── api/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── inference.py         # Load model + run prediction
│   │   └── alert.py             # Alert logic when attack detected
│   └── dashboard/
│       └── app.py               # Streamlit live demo dashboard
│
└── notebooks/
    ├── eda.ipynb
    ├── feature_importance.ipynb
    └── roc_auc_analysis.ipynb
```

## Dataset

### How Data is Collected

Falco records all container syscall events as JSON equally — both normal and attack.
The distinction is made by **controlling when each type of activity occurs** and applying time-based labels afterward.

### Normal Data

- **Workloads:** nginx, redis, webapp (standard open-source images)
- **Traffic generation:** Apache Benchmark (`ab`), redis-cli, custom Python scripts
- **Target volume:** ~30,000 events
- **Label:** `0`

### Attack Data

- **Method:** Simulate 4 MITRE ATT&CK for Containers patterns via bash automation
- **Target volume:** ~20,000 events
- **Label:** `1`

| # | Scenario | MITRE ID | Example Command |
|---|----------|----------|-----------------|
| 1 | Shell execution in container | T1609 | `kubectl exec ... -- /bin/bash -c "id"` |
| 2 | Sensitive file access | T1552 | `find / -name "*.key"` |
| 3 | Network scanning | T1046 | `nmap 10.0.0.0/24` |
| 4 | Privilege escalation attempt | T1611 | `nsenter --target 1 --mount` |

**Always add randomness to prevent uniform patterns:**

```bash
TARGETS=("*.key" "*.pem" "*.env" "*.config")
for i in {1..50}; do
    TARGET=${TARGETS[$RANDOM % ${#TARGETS[@]}]}
    kubectl exec $POD -- find / -name "$TARGET" 2>/dev/null
    sleep $((RANDOM % 5 + 1))   # random interval: 1~5s
done
```

### Auto Labeling

Record attack simulation time ranges → assign `label=1` to events in those windows, `label=0` otherwise.

```python
attack_windows = [
    ("2025-04-26 16:00:00", "2025-04-26 16:30:00"),
    ("2025-04-26 18:30:00", "2025-04-26 19:00:00"),
]

def assign_label(event_time: str) -> int:
    for start, end in attack_windows:
        if start <= event_time <= end:
            return 1
    return 0
```

## Preprocessing

### ⚠️ Critical: Two Different Concepts Named "Label"

| Concept | What it encodes | Values | Stage |
|---------|-----------------|--------|-------|
| **Ground truth label (y)** | Normal vs Attack | 0 = normal, 1 = attack | Auto-labeling |
| **LabelEncoding (feature)** | Categorical features like syscall names | read=0, write=1, execve=2 ... | Preprocessing |

**These are completely separate steps. Do not confuse them.**

### Sliding Window (30s aggregation)

Each window produces **5 features** used as model input:

```python
features = df.groupby(["window", "container_name"]).agg(
    event_count       = ("syscall", "count"),
    unique_syscalls   = ("syscall", "nunique"),
    unique_processes  = ("proc_name", "nunique"),
    critical_count    = ("priority", lambda x: (x == "CRITICAL").sum()),
    sensitive_access  = ("fd_name", lambda x: x.str.contains(
                            "passwd|shadow|key|pem", na=False).sum())
).reset_index()
```

### Train/Test Split

`shuffle=False` is mandatory — this is time-series data. Shuffling causes data leakage.

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, shuffle=False
)
```

## Models

### Strategy: Train Separately, Compare Results

```
Random Forest ──→ train ──→ evaluate ──┐
                                        ├──→ compare → pick best per use case
LSTM ───────────→ train ──→ evaluate ──┘
```

Do **not** ensemble. The goal is to compare which model fits which operational context.

**RF vs LSTM — Key Difference:**

| | Random Forest | LSTM |
|--|---------------|------|
| Input shape | 1 window — `(5,)` | 30 windows — `(30, 5)` |
| Time awareness | None (snapshot) | Learns temporal patterns |
| Best for | Explosive attacks (DDoS) | Slow/stealthy attacks |
| Inference speed | Fast | Moderate |
| Interpretability | High (feature importance) | Low (black box) |

Random Forest uses `n_estimators=200, max_depth=20, random_state=42`. LSTM uses two stacked layers (64 → 32 units) with sigmoid output.

## Evaluation Metrics

Run on the **same held-out test set** for fair comparison.

**Target performance:**

| Metric | Target | Why |
|--------|--------|-----|
| Precision | ≥ 0.90 | Minimize false alarms |
| **Recall** | **≥ 0.95** | **Missing an attack = security incident** |
| F1-score | ≥ 0.90 | Balanced performance |
| FPR | ≤ 0.05 | Operational stability |
| AUC | ≥ 0.95 | Overall discrimination |

> **Recall is the most critical metric.** A missed attack leads to a real breach.

## FastAPI Detection Server

The `/detect` endpoint scales features with the saved scaler, runs inference, and returns `ALERT` when `pred==1` and `prob > 0.8`. Alert threshold is intentionally high (0.8) to reduce false positives while keeping recall priority at training time.

## Coding Rules

- **Always use `random_state=42`** for reproducibility
- **Never `fit` on test data** — `fit_transform` on train, `transform` only on test
- **Never shuffle time-series data** — use `shuffle=False` in train/test split
- **Run attack simulations only inside minikube** — never target external networks
- **Do not commit raw data** — add `data/` and `models/saved/` to `.gitignore`
- **No hardcoded secrets** — use environment variables

## Common Pitfalls

```python
# ❌ Wrong — fitting scaler on test set (data leakage)
scaler.fit_transform(X_test)

# ✅ Correct
scaler.fit_transform(X_train)
scaler.transform(X_test)

# ❌ Wrong — shuffling time-series
train_test_split(X, y, shuffle=True)

# ✅ Correct
train_test_split(X, y, shuffle=False)

# ❌ Wrong — uniform attack pattern (no randomness)
for i in {1..50}; do kubectl exec $POD -- find / -name "*.key"; sleep 2; done

# ✅ Correct — randomized pattern
sleep $((RANDOM % 5 + 1))
```
