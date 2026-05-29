"""Streamlit live demo dashboard for K8s anomaly detection."""

import time
import random
from datetime import datetime, timezone

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/detect"
CONTAINERS = ["nginx", "redis", "webapp"]

st.set_page_config(page_title="K8s Anomaly Detection", layout="wide")
st.title("Kubernetes Runtime Anomaly Detection")

# session state 초기화
if "logs" not in st.session_state:
    st.session_state.logs = []
if "running" not in st.session_state:
    st.session_state.running = False


def random_event(container: str) -> dict:
    is_attack = random.random() < 0.3
    return {
        "container_name":   container,
        "event_count":      random.randint(200, 600) if is_attack else random.randint(10, 100),
        "unique_syscalls":  random.randint(15, 30)   if is_attack else random.randint(3, 10),
        "unique_processes": random.randint(5, 15)    if is_attack else random.randint(1, 4),
        "critical_count":   random.randint(3, 10)    if is_attack else 0,
        "sensitive_access": random.randint(2, 8)     if is_attack else 0,
    }


def call_api(event: dict) -> dict:
    try:
        res = requests.post(API_URL, json=event, timeout=3)
        return res.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 사이드바
with st.sidebar:
    st.header("설정")
    interval = st.slider("탐지 간격 (초)", 1, 10, 2)
    container = st.selectbox("컨테이너", CONTAINERS)
    manual_event = st.expander("수동 입력")
    with manual_event:
        event_count      = st.number_input("event_count",      value=50)
        unique_syscalls  = st.number_input("unique_syscalls",  value=5)
        unique_processes = st.number_input("unique_processes", value=2)
        critical_count   = st.number_input("critical_count",   value=0)
        sensitive_access = st.number_input("sensitive_access", value=0)
        if st.button("탐지 요청"):
            event = {
                "container_name":   container,
                "event_count":      int(event_count),
                "unique_syscalls":  int(unique_syscalls),
                "unique_processes": int(unique_processes),
                "critical_count":   int(critical_count),
                "sensitive_access": int(sensitive_access),
            }
            result = call_api(event)
            st.session_state.logs.insert(0, {
                "time":      datetime.now(timezone.utc).strftime("%H:%M:%S"),
                "container": container,
                "status":    result.get("status", "error"),
                "confidence": result.get("confidence", 0),
                **{k: event[k] for k in event if k != "container_name"},
            })

# 메인 영역
col1, col2, col3 = st.columns(3)
alerts = [l for l in st.session_state.logs if l["status"] == "ALERT"]
normals = [l for l in st.session_state.logs if l["status"] == "normal"]

col1.metric("총 탐지", len(st.session_state.logs))
col2.metric("ALERT", len(alerts), delta=len(alerts) if alerts else None, delta_color="inverse")
col3.metric("정상", len(normals))

st.divider()

# 자동 탐지 토글
if st.button("▶ 자동 탐지 시작" if not st.session_state.running else "⏹ 중지"):
    st.session_state.running = not st.session_state.running

# 최근 이벤트 로그
st.subheader("최근 탐지 로그")
log_placeholder = st.empty()

if st.session_state.running:
    event = random_event(container)
    result = call_api(event)
    st.session_state.logs.insert(0, {
        "time":           datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "container":      container,
        "status":         result.get("status", "error"),
        "confidence":     result.get("confidence", 0),
        "event_count":    event["event_count"],
        "unique_syscalls": event["unique_syscalls"],
        "critical_count": event["critical_count"],
        "sensitive_access": event["sensitive_access"],
    })
    st.session_state.logs = st.session_state.logs[:50]
    time.sleep(interval)
    st.rerun()

if st.session_state.logs:
    import pandas as pd
    df = pd.DataFrame(st.session_state.logs)
    def highlight(row):
        color = "background-color: #ff4b4b; color: white" if row["status"] == "ALERT" else ""
        return [color] * len(row)
    log_placeholder.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)
else:
    log_placeholder.info("탐지 로그 없음 — 자동 탐지를 시작하거나 수동 입력해주세요.")
