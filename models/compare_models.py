#!/usr/bin/env python3
"""Compare RF vs LSTM on the same held-out test set.

RF  : snapshot model — 1 window (5 features)
LSTM: sequential model — 30 windows (seq_len x 5 features)

LSTM uses a subset of test samples (len - seq_len) due to sequence construction,
so metrics are computed on overlapping indices for a fair comparison.
"""

import argparse
import os

import joblib
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved")
SEQ_LEN  = 30
FEATURES = ["event_count", "unique_syscalls", "unique_processes", "critical_count", "sensitive_access"]


def load_data(data_dir: str) -> tuple:
    X_test = np.load(os.path.join(data_dir, "X_test.npy"))
    y_test = np.load(os.path.join(data_dir, "y_test.npy"))
    return X_test, y_test


def make_sequences(X: np.ndarray, y: np.ndarray, seq_len: int) -> tuple:
    xs, ys = [], []
    for i in range(len(X) - seq_len):
        xs.append(X[i : i + seq_len])
        ys.append(y[i + seq_len - 1])
    return np.array(xs), np.array(ys)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        "Precision": precision_score(y_true, y_pred),
        "Recall":    recall_score(y_true, y_pred),
        "F1":        f1_score(y_true, y_pred),
        "FPR":       fp / (fp + tn),
        "AUC":       roc_auc_score(y_true, y_prob),
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
    }


def print_comparison(rf_m: dict, lstm_m: dict) -> None:
    targets = {"Precision": (0.90, "≥"), "Recall": (0.95, "≥"), "F1": (0.90, "≥"),
               "FPR": (0.05, "≤"), "AUC": (0.95, "≥")}

    print("\n" + "=" * 60)
    print(f"{'Metric':<12} {'RF':>10} {'LSTM':>10} {'Target':>10}")
    print("-" * 60)
    for metric, (threshold, op) in targets.items():
        rf_v   = rf_m[metric]
        lstm_v = lstm_m[metric]
        rf_ok   = (rf_v <= threshold) if op == "≤" else (rf_v >= threshold)
        lstm_ok = (lstm_v <= threshold) if op == "≤" else (lstm_v >= threshold)
        print(f"{metric:<12} {rf_v:>9.4f}{'✓' if rf_ok else '✗'}  "
              f"{lstm_v:>9.4f}{'✓' if lstm_ok else '✗'}  "
              f"{op}{threshold}")
    print("=" * 60)

    print(f"\n{'':12} {'RF':>10} {'LSTM':>10}")
    for k in ("TP", "FP", "FN", "TN"):
        print(f"{k:<12} {rf_m[k]:>10} {lstm_m[k]:>10}")

    print("\n[결론]")
    rf_wins   = sum(1 for m, (t, op) in targets.items()
                    if (rf_m[m] <= t if op == "≤" else rf_m[m] >= t))
    lstm_wins = sum(1 for m, (t, op) in targets.items()
                    if (lstm_m[m] <= t if op == "≤" else lstm_m[m] >= t))
    print(f"  RF   목표 달성: {rf_wins}/5")
    print(f"  LSTM 목표 달성: {lstm_wins}/5")
    print()
    print("  RF   → 빠른 탐지, 높은 해석 가능성 (feature importance 활용)")
    print("  LSTM → 느린/스텔스 공격 탐지 적합 (데이터 충분 시 성능 향상 기대)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--save-dir", default=SAVE_DIR)
    args = parser.parse_args()

    print("[compare] loading test data ...")
    X_test, y_test = load_data(args.data_dir)

    # RF — snapshot (all test samples)
    print("[compare] running RF ...")
    rf = joblib.load(os.path.join(args.save_dir, "rf_model.pkl"))
    rf_prob = rf.predict_proba(X_test)[:, 1]
    rf_pred = rf.predict(X_test)

    # LSTM — sequence (test[SEQ_LEN:])
    print("[compare] running LSTM ...")
    lstm = tf.keras.models.load_model(os.path.join(args.save_dir, "lstm_model.keras"))
    X_seq, y_seq = make_sequences(X_test, y_test, SEQ_LEN)
    lstm_prob = lstm.predict(X_seq, verbose=0).flatten()
    lstm_pred = (lstm_prob >= 0.5).astype(int)

    # RF metrics on same indices as LSTM for fair comparison
    rf_m   = compute_metrics(y_test[SEQ_LEN - 1:], rf_pred[SEQ_LEN - 1:], rf_prob[SEQ_LEN - 1:])
    lstm_m = compute_metrics(y_seq, lstm_pred, lstm_prob)

    print_comparison(rf_m, lstm_m)


if __name__ == "__main__":
    main()
