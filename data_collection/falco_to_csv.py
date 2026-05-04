"""
Falco JSON log → CSV 변환기

Usage:
    # Falco가 실시간으로 출력하는 경우 (pipe)
    sudo falco -o json_output=true | python falco_to_csv.py --output events.csv

    # 저장된 로그 파일을 변환하는 경우
    python falco_to_csv.py --input falco.log --output events.csv
"""

import argparse
import csv
import json
import sys
from datetime import datetime

FIELDNAMES = [
    "timestamp",
    "priority",
    "rule",
    "syscall",
    "proc_name",
    "container_name",
    "fd_name",
]


def parse_event(line: str) -> dict | None:
    line = line.strip()
    if not line:
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None

    fields = event.get("output_fields", {})
    return {
        "timestamp":      event.get("time", ""),
        "priority":       event.get("priority", ""),
        "rule":           event.get("rule", ""),
        "syscall":        fields.get("evt.type", ""),
        "proc_name":      fields.get("proc.name", ""),
        "container_name": fields.get("container.name", ""),
        "fd_name":        fields.get("fd.name", ""),
    }


def convert(src, dst_path: str) -> int:
    count = 0
    with open(dst_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for line in src:
            row = parse_event(line)
            if row:
                writer.writerow(row)
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Convert Falco JSON logs to CSV")
    parser.add_argument("--input",  "-i", default=None, help="Input log file (default: stdin)")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file path")
    args = parser.parse_args()

    src = open(args.input, encoding="utf-8") if args.input else sys.stdin
    try:
        count = convert(src, args.output)
    finally:
        if args.input:
            src.close()

    print(f"[falco_to_csv] {count} events written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
