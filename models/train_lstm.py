#!/usr/bin/env python3
"""Train LSTM on preprocessed npy artifacts and save model.

Input shape: (samples, SEQ_LEN=30, features=5)
Each sample is a sliding window of 30 consecutive 30-second windows.
"""

import argparse
import os
import shutil

import joblib
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved")
SEQ_LEN = 30


def load_data(data_dir: str) -> tuple:
    X_train = np.load(os.path.join(data_dir, "X_train.npy"))
    X_test  = np.load(os.path.join(data_dir, "X_test.npy"))
    y_train = np.load(os.path.join(data_dir, "y_train.npy"))
    y_test  = np.load(os.path.join(data_dir, "y_test.npy"))
    return X_train, X_test, y_train, y_test


def make_sequences(X: np.ndarray, y: np.ndarray, seq_len: int) -> tuple:
    """Slide a window of seq_len over time-ordered samples."""
    xs, ys = [], []
    for i in range(len(X) - seq_len):
        xs.append(X[i : i + seq_len])
        ys.append(y[i + seq_len - 1])  # label of the last window in sequence
    return np.array(xs), np.array(ys)


def build_model(seq_len: int, n_features: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(64, return_sequences=True, input_shape=(seq_len, n_features)),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
    )
    return model


def train(model: tf.keras.Model, X_seq: np.ndarray, y_seq: np.ndarray) -> tf.keras.callbacks.History:
    return model.fit(
        X_seq, y_seq,
        epochs=20,
        batch_size=64,
        validation_split=0.1,
        verbose=1,
    )


def evaluate(model: tf.keras.Model, X_seq: np.ndarray, y_seq: np.ndarray) -> None:
    y_prob = model.predict(X_seq, verbose=0).flatten()
    y_pred = (y_prob >= 0.5).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_seq, y_pred).ravel()
    metrics = {
        "Precision": precision_score(y_seq, y_pred),
        "Recall":    recall_score(y_seq, y_pred),
        "F1":        f1_score(y_seq, y_pred),
        "FPR":       fp / (fp + tn),
        "AUC":       roc_auc_score(y_seq, y_prob),
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


def save_model(model: tf.keras.Model, save_dir: str, data_dir: str) -> None:
    os.makedirs(save_dir, exist_ok=True)

    model_path = os.path.join(save_dir, "lstm_model.keras")
    model.save(model_path)
    print(f"\n[train_lstm] model saved → {model_path}")

    scaler_src = os.path.join(data_dir, "scaler.pkl")
    scaler_dst = os.path.join(save_dir, "scaler.pkl")
    if not os.path.exists(scaler_dst):
        shutil.copy2(scaler_src, scaler_dst)
        print(f"[train_lstm] scaler copied → {scaler_dst}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--save-dir", default=SAVE_DIR)
    parser.add_argument("--seq-len", type=int, default=SEQ_LEN)
    args = parser.parse_args()

    print("[train_lstm] loading data ...")
    X_train, X_test, y_train, y_test = load_data(args.data_dir)
    print(f"  train: {X_train.shape}  test: {X_test.shape}")

    print(f"[train_lstm] building sequences (seq_len={args.seq_len}) ...")
    X_train_seq, y_train_seq = make_sequences(X_train, y_train, args.seq_len)
    X_test_seq,  y_test_seq  = make_sequences(X_test,  y_test,  args.seq_len)
    print(f"  train seq: {X_train_seq.shape}  test seq: {X_test_seq.shape}")

    if len(X_train_seq) == 0:
        raise ValueError(
            f"학습 샘플이 없습니다. seq_len({args.seq_len})이 "
            f"train 샘플 수({len(X_train)})보다 큽니다. --seq-len을 줄이세요."
        )

    print("[train_lstm] building model ...")
    model = build_model(args.seq_len, X_train.shape[1])
    model.summary()

    print("[train_lstm] training ...")
    train(model, X_train_seq, y_train_seq)

    evaluate(model, X_test_seq, y_test_seq)
    save_model(model, args.save_dir, args.data_dir)


if __name__ == "__main__":
    main()
