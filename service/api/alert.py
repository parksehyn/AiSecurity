"""Alert logic when attack is detected."""

import os
from datetime import datetime, timezone


ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "0.8"))


def should_alert(pred: int, prob: float) -> bool:
    return pred == 1 and prob >= ALERT_THRESHOLD


def build_alert(container_name: str, prob: float) -> dict:
    return {
        "status":     "ALERT",
        "container":  container_name,
        "confidence": round(prob, 3),
        "action":     "pod isolation recommended",
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }


def build_normal(prob: float) -> dict:
    return {
        "status":     "normal",
        "confidence": round(prob, 3),
    }
