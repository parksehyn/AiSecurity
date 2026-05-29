#!/usr/bin/env python3
"""labeled.csv → X_train/test.npy + y_train/test.npy + scaler.pkl + encoders.pkl"""

import argparse
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
WINDOW_SECS = 30
FEATURES = ["event_count", "unique_syscalls", "unique_processes", "critical_count", "sensitive_access"]
SENSITIVE_PAT = r"passwd|shadow|key|pem"
CAT_COLS = ["syscall", "proc_name", "container_name"]


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    return df


def encode_categoricals(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    encoders = {}
    for col in CAT_COLS:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].fillna("unknown").astype(str))
        encoders[col] = le
    return df, encoders


def make_windows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    origin = df["timestamp"].min().floor("s")
    df["window"] = ((df["timestamp"] - origin).dt.total_seconds() // WINDOW_SECS).astype(int)

    agg = (
        df.groupby(["window", "container_name"])
        .agg(
            event_count=("syscall", "count"),
            unique_syscalls=("syscall", "nunique"),
            unique_processes=("proc_name", "nunique"),
            critical_count=("priority", lambda x: x.str.lower().eq("critical").sum()),
            sensitive_access=("fd_name", lambda x: x.fillna("").str.contains(SENSITIVE_PAT, case=False, na=False).sum()),
            label=("label", "max"),
        )
        .reset_index()
        .sort_values("window")
    )
    return agg


def split_and_scale(windows: pd.DataFrame) -> dict:
    X = windows[FEATURES].values
    y = windows["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False, stratify=None
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    return {"X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test, "scaler": scaler}


def save(artifacts: dict, encoders: dict, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name in ("X_train", "X_test", "y_train", "y_test"):
        np.save(os.path.join(out_dir, f"{name}.npy"), artifacts[name])
    with open(os.path.join(out_dir, "scaler.pkl"), "wb") as f:
        pickle.dump(artifacts["scaler"], f)
    with open(os.path.join(out_dir, "encoders.pkl"), "wb") as f:
        pickle.dump(encoders, f)


def report(windows: pd.DataFrame, artifacts: dict) -> None:
    total = len(windows)
    attack = windows["label"].sum()
    print(f"windows total : {total}")
    print(f"  attack (1)  : {attack} ({attack/total:.1%})")
    print(f"  normal (0)  : {total-attack} ({(total-attack)/total:.1%})")
    print(f"train / test  : {len(artifacts['X_train'])} / {len(artifacts['X_test'])}")
    print(f"features      : {FEATURES}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=os.path.join(DATA_DIR, "labeled.csv"))
    parser.add_argument("--output-dir", default=DATA_DIR)
    args = parser.parse_args()

    print(f"[preprocess] loading {args.input} ...")
    df = load(args.input)
    print(f"  rows: {len(df):,}  |  attack={df['label'].sum():,}  normal={(df['label']==0).sum():,}")

    print("[preprocess] encoding categoricals ...")
    df, encoders = encode_categoricals(df)

    print("[preprocess] building 30-second windows ...")
    windows = make_windows(df)

    print("[preprocess] splitting and scaling ...")
    artifacts = split_and_scale(windows)

    print("[preprocess] saving artifacts ...")
    save(artifacts, encoders, args.output_dir)

    report(windows, artifacts)
    print(f"[preprocess] done → {args.output_dir}")


if __name__ == "__main__":
    main()
