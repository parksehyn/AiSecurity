"""FastAPI entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .alert import build_alert, build_normal, should_alert
from .inference import is_loaded, load, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    load()
    yield


app = FastAPI(title="K8s Anomaly Detection API", lifespan=lifespan)


class EventWindow(BaseModel):
    container_name:   str
    event_count:      int = Field(default=0, ge=0)
    unique_syscalls:  int = Field(default=0, ge=0)
    unique_processes: int = Field(default=0, ge=0)
    critical_count:   int = Field(default=0, ge=0)
    sensitive_access: int = Field(default=0, ge=0)


@app.get("/health")
def health():
    if not is_loaded():
        raise HTTPException(status_code=503, detail="model not loaded")
    return {"status": "ok"}


@app.post("/detect")
def detect(event: EventWindow):
    try:
        pred, prob = predict(event.model_dump())
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    if should_alert(pred, prob):
        return build_alert(event.container_name, prob)
    return build_normal(prob)
