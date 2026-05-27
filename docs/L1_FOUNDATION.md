---
level: L1
protection: 수정 시 사람이 직접 명시 승인 필요
---

# L1 Foundation — 절대 안 바뀌는 기반

> 이 문서는 프로젝트의 존재 이유와 불변 원칙을 정의한다.
> 수정은 팀원 명시 승인 없이 불가능하다. Claude도 이 문서를 수정하지 않는다.

---

## 해결하려는 문제

Kubernetes 클러스터에서 컨테이너 런타임 이상 행동을 **실시간으로 탐지**한다.
Falco가 수집한 syscall 이벤트를 ML 모델로 분석해 공격 여부를 판별한다.

**핵심 목표:** 공격 미탐지(False Negative)를 최소화한다.
공격을 놓치는 것은 실제 시스템 침해로 이어진다.

---

## 불변 제약 (Invariants)

이 제약들은 어떤 코드에서도 예외 없이 적용된다.

| 제약 | 이유 |
|------|------|
| `Recall ≥ 0.95` 최우선 | 공격 미탐지 = 실제 침해 |
| `shuffle=False` | 시계열 데이터 — 시간 순서 뒤섞으면 데이터 누수 |
| `random_state=42` 고정 | 재현 가능성 보장 |
| RF / LSTM 앙상블 금지 | 별도 학습·비교가 목적 |
| 스케일러 `fit`은 train에만 | test에 fit하면 데이터 누수 |
| `container_name == 'host'` 필터링 | 호스트 OS 이벤트는 학습 대상 아님 |
| `data/`, `models/saved/` 커밋 금지 | 원시 데이터·모델 파일은 git 제외 |
| `.env` 커밋 금지 | 시크릿 노출 방지 |
| 공격 시뮬레이션은 격리된 환경(minikube 또는 VM Docker) 내부에서만 | 실제 환경 오염 방지 |

---

## Git Workflow

```
feature/<name> 브랜치에서 개발
    → pytest 통과
    → PR 생성 (feat: <기능명> (#<이슈번호>))
    → main 머지
main 직접 커밋 금지
```

**이슈 형식:** 개요 / 작업 범위(체크리스트) / 완료 기준 / 참고(브랜치명)
**PR 형식:** 개요 + `Closes #n` / 변경 사항 / 테스트 결과 / 미완료

---

## How Claude Should Work

- 불확실하면 가정하지 말고 먼저 물어본다
- 요청한 것만 구현한다 — 추측성 기능, 불필요한 추상화 금지
- 기존 코드는 요청과 직접 관련된 줄만 수정한다
- 멀티스텝 작업은 계획을 먼저 제시하고 각 단계를 검증한다
- 작업 전 반드시 doc-guardian으로 문서 모순·모호성 확인

---

## 워크플로우 (불변)

```
업무 지시
    ↓
[doc-guardian]   docs/ 전체 정독 → 모순·모호성 체크
    ↓
[architect]      플랜 작성 (코드 없이 설계만)
    ↓
[부모 Claude]    코드 수정 (유일한 Write 권한)
    ↓
[code-reviewer]  diff 리뷰 (read-only)
    ↓
[qa-validator]   QA 분석 → 부모 Claude가 테스트 실행
    ↓
    반복
    ↓
개발 완료 → [doc-guardian] 파급 체크 → 문서 업데이트 → 커밋 → PR
```
