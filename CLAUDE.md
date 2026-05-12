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

## 핵심 설계 결정

**레이블 혼동 주의:** ground truth label(0=정상, 1=공격)과 LabelEncoding(범주형 피처 인코딩)은 완전히 별개의 단계다.

**모델 전략:** RF(1 window 스냅샷, 빠른 탐지)와 LSTM(30 window 시퀀스, 은닉 공격)을 별도 학습 후 비교. 앙상블 금지.

**평가 우선순위:** Recall ≥ 0.95 최우선 — 공격 미탐지는 실제 침해로 이어진다.
