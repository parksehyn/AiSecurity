"""
data_collection 모듈 테스트
mock 데이터 기반 — Falco/minikube 환경 불필요
"""

import csv
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from falco_to_csv import parse_event, convert
from auto_labeling import parse_windows, assign_label, label_csv


# ─── falco_to_csv 테스트 ──────────────────────────────────────────────────────

class TestParseEvent(unittest.TestCase):

    def _make_event(self, **overrides):
        base = {
            "time": "2025-04-26T16:05:00.000000000Z",
            "priority": "WARNING",
            "rule": "Terminal shell in container",
            "output_fields": {
                "evt.type":        "execve",
                "proc.name":       "bash",
                "container.name":  "webapp",
                "fd.name":         "",
            },
        }
        base.update(overrides)
        return json.dumps(base)

    def test_valid_event(self):
        row = parse_event(self._make_event())
        self.assertEqual(row["priority"], "WARNING")
        self.assertEqual(row["syscall"], "execve")
        self.assertEqual(row["proc_name"], "bash")
        self.assertEqual(row["container_name"], "webapp")

    def test_empty_line_returns_none(self):
        self.assertIsNone(parse_event(""))
        self.assertIsNone(parse_event("   "))

    def test_invalid_json_returns_none(self):
        self.assertIsNone(parse_event("not json at all"))

    def test_missing_output_fields_uses_empty_string(self):
        raw = json.dumps({"time": "2025-01-01T00:00:00Z", "priority": "INFO", "rule": "x"})
        row = parse_event(raw)
        self.assertEqual(row["syscall"], "")
        self.assertEqual(row["proc_name"], "")

    def test_sensitive_fd_name_preserved(self):
        line = self._make_event(output_fields={
            "evt.type": "open",
            "proc.name": "cat",
            "container.name": "webapp",
            "fd.name": "/etc/shadow",
        })
        row = parse_event(line)
        self.assertEqual(row["fd_name"], "/etc/shadow")


class TestConvert(unittest.TestCase):

    def _make_lines(self, n=5, priority="WARNING"):
        lines = []
        for i in range(n):
            lines.append(json.dumps({
                "time": f"2025-04-26T16:0{i}:00.000000000Z",
                "priority": priority,
                "rule": "test rule",
                "output_fields": {
                    "evt.type": "read",
                    "proc.name": "nginx",
                    "container.name": "web",
                    "fd.name": f"/var/log/access{i}.log",
                },
            }))
        return lines

    def test_convert_writes_correct_row_count(self):
        lines = self._make_lines(10)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            dst = f.name
        try:
            count = convert(iter(lines), dst)
            self.assertEqual(count, 10)
            with open(dst) as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 10)
        finally:
            os.unlink(dst)

    def test_convert_skips_invalid_lines(self):
        lines = self._make_lines(3) + ["bad line", "", "{}"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            dst = f.name
        try:
            count = convert(iter(lines), dst)
            self.assertEqual(count, 3)
        finally:
            os.unlink(dst)

    def test_csv_has_all_fieldnames(self):
        lines = self._make_lines(1)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            dst = f.name
        try:
            convert(iter(lines), dst)
            with open(dst) as f:
                reader = csv.DictReader(f)
                self.assertSetEqual(
                    set(reader.fieldnames),
                    {"timestamp", "priority", "rule", "syscall", "proc_name", "container_name", "fd_name"},
                )
        finally:
            os.unlink(dst)


# ─── auto_labeling 테스트 ─────────────────────────────────────────────────────

class TestParseWindows(unittest.TestCase):

    def test_single_window(self):
        windows = parse_windows(["2025-04-26 16:00:00,2025-04-26 16:30:00"])
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0][0], datetime(2025, 4, 26, 16, 0, 0))
        self.assertEqual(windows[0][1], datetime(2025, 4, 26, 16, 30, 0))

    def test_multiple_windows(self):
        windows = parse_windows([
            "2025-04-26 16:00:00,2025-04-26 16:30:00",
            "2025-04-26 18:30:00,2025-04-26 19:00:00",
        ])
        self.assertEqual(len(windows), 2)


class TestAssignLabel(unittest.TestCase):

    def setUp(self):
        self.windows = [
            (datetime(2025, 4, 26, 16, 0, 0), datetime(2025, 4, 26, 16, 30, 0)),
            (datetime(2025, 4, 26, 18, 30, 0), datetime(2025, 4, 26, 19, 0, 0)),
        ]

    def test_inside_first_window_is_attack(self):
        self.assertEqual(assign_label(datetime(2025, 4, 26, 16, 15, 0), self.windows), 1)

    def test_inside_second_window_is_attack(self):
        self.assertEqual(assign_label(datetime(2025, 4, 26, 18, 45, 0), self.windows), 1)

    def test_boundary_start_is_attack(self):
        self.assertEqual(assign_label(datetime(2025, 4, 26, 16, 0, 0), self.windows), 1)

    def test_boundary_end_is_attack(self):
        self.assertEqual(assign_label(datetime(2025, 4, 26, 16, 30, 0), self.windows), 1)

    def test_before_window_is_normal(self):
        self.assertEqual(assign_label(datetime(2025, 4, 26, 15, 59, 59), self.windows), 0)

    def test_between_windows_is_normal(self):
        self.assertEqual(assign_label(datetime(2025, 4, 26, 17, 0, 0), self.windows), 0)

    def test_after_all_windows_is_normal(self):
        self.assertEqual(assign_label(datetime(2025, 4, 26, 20, 0, 0), self.windows), 0)


class TestLabelCsv(unittest.TestCase):

    def _write_csv(self, rows, path):
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "priority", "rule", "syscall",
                                                    "proc_name", "container_name", "fd_name"])
            writer.writeheader()
            writer.writerows(rows)

    def test_label_ratio_correct(self):
        rows = [
            {"timestamp": "2025-04-26 16:10:00", "priority": "WARNING", "rule": "r",
             "syscall": "execve", "proc_name": "bash", "container_name": "web", "fd_name": ""},
            {"timestamp": "2025-04-26 17:00:00", "priority": "INFO", "rule": "r",
             "syscall": "read",  "proc_name": "nginx", "container_name": "web", "fd_name": ""},
            {"timestamp": "2025-04-26 18:40:00", "priority": "WARNING", "rule": "r",
             "syscall": "open",  "proc_name": "cat",   "container_name": "web", "fd_name": "/etc/shadow"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as fin, \
             tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as fout:
            in_path, out_path = fin.name, fout.name

        try:
            self._write_csv(rows, in_path)
            windows = [
                (datetime(2025, 4, 26, 16, 0, 0), datetime(2025, 4, 26, 16, 30, 0)),
                (datetime(2025, 4, 26, 18, 30, 0), datetime(2025, 4, 26, 19, 0, 0)),
            ]
            label_csv(in_path, out_path, windows)

            import pandas as pd
            df = pd.read_csv(out_path)
            self.assertEqual(df["label"].sum(), 2)       # 2개 attack
            self.assertEqual((df["label"] == 0).sum(), 1) # 1개 normal
        finally:
            os.unlink(in_path)
            os.unlink(out_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
