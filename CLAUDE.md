# CLAUDE.md — 프로젝트 인덱스

Kubernetes 런타임 이상 탐지 시스템.
Falco syscall 수집 → RF/LSTM 학습 → FastAPI + Streamlit 제공.

---

## 문서 구조

| 레벨 | 파일 | 내용 | 수정 |
|------|------|------|------|
| **L1** | `docs/L1_FOUNDATION.md` | 문제 정의, 불변 제약, 워크플로우 | 사람 명시 승인 필요 |
| **L2** | `docs/L2_ARCHITECTURE.md` | 파이프라인, 스키마, 모델 전략, 설계 결정 | 수정 후 L3 파급 체크 필수 |
| **L3** | `docs/L3_PROGRESS.md` | 현재 진행 상황, 다음 단계, 미결 사항 | 자유롭게 수정 |

> **작업 시작 전:** 반드시 L1 → L2 → L3 순서로 정독. doc-guardian으로 모순 체크.

---

## 빠른 커맨드

```bash
pytest data_collection/ -v

python data_collection/falco_to_csv.py --input falco.log --output events.csv

python data_collection/auto_labeling.py \
    --input events.csv --output labeled.csv \
    --attack-windows "2025-04-26 16:00:00,2025-04-26 16:30:00"
```

---

## 에이전트

| 에이전트 | 역할 | 권한 |
|----------|------|------|
| `doc-guardian` | 문서 모순·모호성 감시, 파급 체크 | read-only |
| `architect` | ML 파이프라인 설계·플래닝 | read-only |
| `code-reviewer` | diff 리뷰, ML 규칙 체크 | read-only |
| `qa-validator` | 테스트 케이스 분석, 버그 발견 | read-only |
| `lab-experimenter` | 실험 코드 작성 | lab/ 한정 write |

**부모 Claude만 실제 소스 코드를 수정한다.**
