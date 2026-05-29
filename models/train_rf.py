#!/usr/bin/env python3
"""Train Random Forest on preprocessed npy artifacts and save model."""

import argparse
import os
import shutil

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved")


def load_data(data_dir: str) -> tuple:
    X_train = np.load(os.path.join(data_dir, "X_train.npy"))
    X_test  = np.load(os.path.join(data_dir, "X_test.npy"))
    y_train = np.load(os.path.join(data_dir, "y_train.npy"))
    y_test  = np.load(os.path.join(data_dir, "y_test.npy"))
    return X_train, X_test, y_train, y_test


def train(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def evaluate(model: RandomForestClassifier, X_test: np.ndarray, y_test: np.ndarray) -> None:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    metrics = {
        "Precision": precision_score(y_test, y_pred),
        "Recall":    recall_score(y_test, y_pred),
        "F1":        f1_score(y_test, y_pred),
        "FPR":       fp / (fp + tn),
        "AUC":       roc_auc_score(y_test, y_prob),
    }

    print("\n[evaluate] results")
    for k, v in metrics.items():
        target_met = _check_target(k, v)
        print(f"  {k:<12}: {v:.4f}  {'✓' if target_met else '✗'}")
    print(f"\n  confusion matrix: TP={tp} FP={fp} FN={fn} TN={tn}")


def _check_target(metric: str, value: float) -> bool:
    targets = {"Precision": 0.90, "Recall": 0.95, "F1": 0.90, "FPR": 0.05, "AUC": 0.95}
    if metric == "FPR":
        return value <= targets[metric]
    return value >= targets.get(metric, 0)


def save_model(model: RandomForestClassifier, save_dir: str, data_dir: str) -> None:
    os.makedirs(save_dir, exist_ok=True)

    model_path = os.path.join(save_dir, "rf_model.pkl")
    joblib.dump(model, model_path)
    print(f"\n[train_rf] model saved → {model_path}")

    scaler_src = os.path.join(data_dir, "scaler.pkl")
    scaler_dst = os.path.join(save_dir, "scaler.pkl")
    shutil.copy2(scaler_src, scaler_dst)
    print(f"[train_rf] scaler copied → {scaler_dst}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--save-dir", default=SAVE_DIR)
    args = parser.parse_args()

    print("[train_rf] loading data ...")
    X_train, X_test, y_train, y_test = load_data(args.data_dir)
    print(f"  train: {X_train.shape}  test: {X_test.shape}")

    print("[train_rf] training ...")
    model = train(X_train, y_train)

    evaluate(model, X_test, y_test)
    save_model(model, args.save_dir, args.data_dir)


if __name__ == "__main__":
    main()
