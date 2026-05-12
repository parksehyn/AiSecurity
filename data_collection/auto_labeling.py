"""
시간 기반 자동 레이블링

attack_windows 범위 내 이벤트 → label=1, 나머지 → label=0

Usage:
    python auto_labeling.py --input events.csv --output labeled.csv \\
        --attack-windows "2025-04-26 16:00:00,2025-04-26 16:30:00" \\
                         "2025-04-26 18:30:00,2025-04-26 19:00:00"
"""

import argparse
import pandas as pd
from datetime import datetime


def parse_windows(raw: list[str]) -> list[tuple[datetime, datetime]]:
    windows = []
    for entry in raw:
        start_str, end_str = entry.split(",")
        start = datetime.fromisoformat(start_str.strip().replace("Z", "+00:00")).replace(tzinfo=None)
        end = datetime.fromisoformat(end_str.strip().replace("Z", "+00:00")).replace(tzinfo=None)
        windows.append((start, end))
    return windows


def assign_label(ts: datetime, windows: list[tuple[datetime, datetime]]) -> int:
    for start, end in windows:
        if start <= ts <= end:
            return 1
    return 0


def label_csv(input_path: str, output_path: str, windows: list[tuple[datetime, datetime]]) -> None:
    df = pd.read_csv(input_path)

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(None)
    df["label"] = df["timestamp"].apply(lambda ts: assign_label(ts, windows))

    df.to_csv(output_path, index=False)

    total   = len(df)
    attacks = df["label"].sum()
    print(f"[auto_labeling] total={total}  attack={attacks}  normal={total - attacks}")
    print(f"[auto_labeling] labeled CSV → {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Assign labels based on attack time windows")
    parser.add_argument("--input",          "-i", required=True,  help="Input CSV from falco_to_csv.py")
    parser.add_argument("--output",         "-o", required=True,  help="Output labeled CSV")
    parser.add_argument("--attack-windows", "-w", nargs="+", required=True,
                        help='Attack windows as "YYYY-MM-DD HH:MM:SS,YYYY-MM-DD HH:MM:SS"')
    args = parser.parse_args()

    windows = parse_windows(args.attack_windows)
    label_csv(args.input, args.output, windows)


if __name__ == "__main__":
    main()
