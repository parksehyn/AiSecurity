---
level: L3
protection: 자유롭게 수정 가능
---

# L3 Progress — 현재 진행 상황

> 주간 업무, 진행 상황, 다음 단계를 기록한다.
> 자유롭게 수정 가능. 세션 종료 시 /handoff로 업데이트.

---

## 현재 브랜치
`feature/dashboard` (Streamlit 대시보드 진행 중)

---

## 완료 항목

- [x] `feature/data-collection`: `falco_to_csv.py`, `auto_labeling.py`, `normal_traffic_docker.sh`, `attack_simulator_docker.sh`, `collect_loop.sh`
- [x] `fix/ec2-setup-clone-branch`: `ec2_setup.sh` 수정 (브랜치명, Falco file_output, sg 제거, watchdog)
- [x] VirtualBox Ubuntu 26.04 VM 신규 설치 — Docker, Falco Modern eBPF, nginx/redis 컨테이너 세팅 완료
- [x] **데이터 수집 완료** — 8라운드 collect_loop.sh 실행 (VM 종료로 중단), labeled.csv 생성 → `data/labeled.csv` 로컬 확보
- [x] `scripts/falco_watchdog.sh` 추가 — Falco 크래시 시 자동 재시작
- [x] `preprocessing/preprocess.py` 작성 — 단일 스크립트로 전처리 전 단계 처리
- [x] `preprocessing/preprocess.py` VM 실행 완료 — 397 윈도우, train/test 317/80
- [x] `models/train_rf.py` 작성 및 VM 실행 — 전 지표 목표 달성 (Precision 0.95 / Recall 0.95 / F1 0.95 / FPR 0.017 / AUC 0.996)
- [x] `models/train_lstm.py` 작성 및 Colab 실행 — 2/5 목표 달성 (데이터 부족, RF 우세 확인)
- [x] `models/compare_models.py` 작성 — RF vs LSTM 나란히 비교, RF 우세 결론 도출
- [x] `service/api/` 작성 — FastAPI `/detect`, `/health` 엔드포인트 로컬 실행 확인

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

### Step 1: Streamlit 대시보드 (`service/dashboard/app.py`)
- FastAPI `/detect` 엔드포인트 연동
- 실시간 탐지 결과 시각화
- 최근 이벤트 로그 테이블

---

## 한계 및 관찰

| 항목 | 내용 |
|------|------|
| 윈도우 수 부족 | 397개 윈도우로 RF 결정 경계 불안정 — `unique_processes=1` 같은 정상 패턴도 공격으로 오분류 가능 |
| LSTM 성능 미달 | 시퀀스 구성 후 test 샘플 50개로 통계 불안정, 데이터 추가 시 개선 여지 있음 |
| 데이터 편향 | 공격 시뮬레이션이 특정 패턴에 집중 — 실제 공격 다양성 미반영 |

> 데이터 수집량 증가(목표 50,000 윈도우 이상) 시 위 한계 해소 가능

## 미결 사항

- minikube, helm 미설치 (서비스 배포 단계에서 도입 예정)

---

## 향후 개선 방향

### 단기 (1~2주)

| 항목 | 내용 | 효과 |
|------|------|------|
| RF 오탐 완화 | `min_samples_leaf=5`, `min_samples_split=10` 추가 | FPR 안정화 |
| 피처 보강 | syscall 발생 간격 평균값(`avg_interval`) 추가 | burst vs slow 패턴 구분 |

### 중기 (1개월)

| 항목 | 내용 | 효과 |
|------|------|------|
| 데이터 증강 | 윈도우 2,000개 이상 확보 | LSTM 포함 전 지표 달성 근본 해결 |
| LSTM 시퀀스 분리 | container_name별 독립 시퀀스 구성 | LSTM Recall 0.95 달성 가능성 |
| LSTM 서빙 추가 | FastAPI `/detect/lstm` 엔드포인트 | 스텔스 공격 커버 |
| 공격 패턴 확장 | T1070(로그 삭제), T1496(크립토마이닝) 추가 | 모델 일반화 |

### 장기 (3개월+)

| 항목 | 내용 | 효과 |
|------|------|------|
| minikube 실 배포 | Falco DaemonSet + FastAPI Deployment | 실 k8s 환경 검증 |
| SHAP 설명 추가 | 탐지 근거 피처 상위 2개 응답에 포함 | 운영 신뢰성 |
| 온라인 학습 | Falco 스트리밍 → 롤링 윈도우 → 자동 재학습 | 새 공격 패턴 적응 |

---

## 필수 설치 상태

| 도구 | 상태 |
|------|------|
| minikube | ❌ 미설치 |
| helm | ❌ 미설치 |
| kubectl | ✅ 완료 |
| docker | ✅ 완료 (VM) |
| falco | ✅ 완료 (VM, watchdog 포함) |
