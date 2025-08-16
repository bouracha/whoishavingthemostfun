#!/usr/bin/env python3
"""
Compare simulated data CSVs line-by-line between:
  - database/chess
  - database/test_data/chess

Exact match required: same files, same ordering, identical contents.

Exit code:
  - 0 on exact match
  - 1 on any mismatch (prints concise diagnostics)
"""

import os
import sys


def list_csv_files(directory: str) -> set:
    if not os.path.isdir(directory):
        return set()
    return {f for f in os.listdir(directory) if f.endswith('.csv')}


def read_lines(path: str) -> list:
    with open(path, 'r', encoding='utf-8') as fh:
        lines = fh.read().splitlines()
    
    # If this is a CSV with timestamp column, zero out the timestamps
    if lines and 'timestamp' in lines[0].lower():
        header = lines[0]
        data_lines = lines[1:]
        
        # Find timestamp column index
        headers = header.split(',')
        try:
            timestamp_idx = next(i for i, h in enumerate(headers) if 'timestamp' in h.lower())
        except StopIteration:
            return lines  # No timestamp column found
        
        # Zero out timestamps in data lines
        processed_lines = [header]
        for line in data_lines:
            if line.strip():  # Skip empty lines
                parts = line.split(',')
                if len(parts) > timestamp_idx:
                    parts[timestamp_idx] = '2024-01-01 00:00:00'  # Zero out timestamp
                processed_lines.append(','.join(parts))
        
        return processed_lines
    
    return lines


def compare_files_line_by_line(file_a: str, file_b: str) -> tuple[bool, str]:
    lines_a = read_lines(file_a)
    lines_b = read_lines(file_b)

    if len(lines_a) != len(lines_b):
        return False, f"line count differs ({len(lines_a)} vs {len(lines_b)})"

    for idx, (la, lb) in enumerate(zip(lines_a, lines_b), start=1):
        if la != lb:
            return False, f"first diff at line {idx}\n  A: {la}\n  B: {lb}"

    return True, ""


def main() -> int:
    base = os.path.dirname(__file__)
    live_dir = os.path.join(base, 'database', 'chess')
    snap_dir = os.path.join(base, 'database', 'test_data', 'chess')

    # Basic existence checks
    if not os.path.isdir(live_dir):
        print(f"❌ Missing directory: {live_dir}")
        return 1
    if not os.path.isdir(snap_dir):
        print(f"❌ Missing directory: {snap_dir}")
        return 1

    live_csvs = list_csv_files(live_dir)
    snap_csvs = list_csv_files(snap_dir)

    if live_csvs != snap_csvs:
        only_in_live = sorted(live_csvs - snap_csvs)
        only_in_snap = sorted(snap_csvs - live_csvs)
        if only_in_live:
            print(f"❌ Files only in {live_dir}: {only_in_live}")
        if only_in_snap:
            print(f"❌ Files only in {snap_dir}: {only_in_snap}")
        return 1

    # Deterministic order
    all_files = sorted(live_csvs)

    any_diff = False
    for fname in all_files:
        a = os.path.join(live_dir, fname)
        b = os.path.join(snap_dir, fname)
        ok, detail = compare_files_line_by_line(a, b)
        if not ok:
            any_diff = True
            print(f"❌ {fname} differs: {detail}")
        else:
            print(f"✅ {fname} matches")

    if any_diff:
        return 1

    print("\n✅ All chess CSVs match exactly")
    return 0


if __name__ == '__main__':
    sys.exit(main())


