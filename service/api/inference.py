"""Load model + scaler and run prediction."""

import os

import joblib
import numpy as np

SAVE_DIR = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "models", "saved"))
FEATURES = ["event_count", "unique_syscalls", "unique_processes", "critical_count", "sensitive_access"]

_model  = None
_scaler = None


def load():
    global _model, _scaler
    try:
        _model  = joblib.load(os.path.join(SAVE_DIR, "rf_model.pkl"))
        _scaler = joblib.load(os.path.join(SAVE_DIR, "scaler.pkl"))
    except FileNotFoundError as e:
        raise RuntimeError(f"Model file not found: {e}") from e


def is_loaded() -> bool:
    return _model is not None


def predict(event: dict) -> tuple[int, float]:
    """Return (pred, prob) for a single event window."""
    features = [event.get(f, 0) for f in FEATURES]
    scaled = _scaler.transform([features])
    pred = int(_model.predict(scaled)[0])
    prob = float(_model.predict_proba(scaled)[0][1])
    return pred, prob
