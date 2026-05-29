"""FastAPI entry point."""

from fastapi import FastAPI
from pydantic import BaseModel

from .alert import build_alert, build_normal, should_alert
from .inference import predict

app = FastAPI(title="K8s Anomaly Detection API")


class EventWindow(BaseModel):
    container_name:   str
    event_count:      int   = 0
    unique_syscalls:  int   = 0
    unique_processes: int   = 0
    critical_count:   int   = 0
    sensitive_access: int   = 0


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/detect")
def detect(event: EventWindow):
    pred, prob = predict(event.model_dump())
    if should_alert(pred, prob):
        return build_alert(event.container_name, prob)
    return build_normal(prob)
