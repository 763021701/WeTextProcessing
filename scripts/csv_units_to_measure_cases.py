#!/usr/bin/env python3
# Copyright 2026 (script for WeTextProcessing)
# Convert raw/all_units_with_pronunciation.csv to measure.txt-style lines:
#   <Chinese pronunciation> => <expected unit string>
#
# Usage:
#   python scripts/csv_units_to_measure_cases.py \
#       [--input raw/all_units_with_pronunciation.csv] \
#       [--output itn/chinese/test/data/units_pronunciation_from_csv.txt]
#
# Batch ITN test (many cases may fail until rules cover them):
#   ITN_TEST_CSV_UNITS=1 python -m pytest itn/chinese/test/test_units_csv.py -q

import argparse
import csv
import os
import re


def _split_units(unit: str) -> list[str]:
    unit = unit.strip()
    if not unit:
        return []
    # e.g. ng/dl：ng/ml.h in source CSV
    if "：" in unit:
        parts = [x.strip() for x in unit.split("：") if x.strip()]
        if len(parts) > 1:
            return parts
    for sep in (";", "；"):
        if sep in unit:
            return [x.strip() for x in unit.split(sep) if x.strip()]
    # "Kcal/24h, kJ/24h" style (comma between unit tokens, not thousands)
    if "," in unit and re.search(r"[A-Za-z/]", unit):
        parts = [x.strip() for x in unit.split(",") if x.strip()]
        if len(parts) > 1:
            return parts
    return [unit]


def _split_pronunciations(pron: str) -> list[str]:
    pron = pron.strip().replace("，", ",")
    if not pron:
        return []
    for sep in (";", "；", ","):
        if sep in pron:
            parts = [x.strip() for x in pron.split(sep) if x.strip()]
            if len(parts) > 1:
                return parts
    return [pron]


def expand_pairs(unit: str, pronunciation: str) -> list[tuple[str, str]]:
    """Return list of (spoken_chinese, expected_unit)."""
    unit = (unit or "").strip()
    pronunciation = (pronunciation or "").strip()
    if not unit or not pronunciation:
        return []

    units = _split_units(unit)
    prons = _split_pronunciations(pronunciation)

    if len(units) == len(prons):
        return list(zip(prons, units))
    if len(units) == 1:
        return [(p, units[0]) for p in prons]
    if len(prons) == 1:
        return [(prons[0], u) for u in units]
    # Mismatch: keep one combined line so nothing is silently dropped
    return [(pronunciation, unit)]


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="CSV unit/pronunciation -> measure.txt format")
    ap.add_argument(
        "--input",
        default=os.path.join(root, "raw", "all_units_with_pronunciation.csv"),
        help="Source CSV (columns: unit,count,pronunciation)",
    )
    ap.add_argument(
        "--output",
        default=os.path.join(root, "itn", "chinese", "test", "data", "units_pronunciation_from_csv.txt"),
        help="Output path (same line format as measure.txt)",
    )
    args = ap.parse_args()

    seen: set[tuple[str, str]] = set()
    lines_out: list[str] = []

    with open(args.input, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or [c.strip().lower() for c in header[:3]] != ["unit", "count", "pronunciation"]:
            raise SystemExit(f"Unexpected CSV header: {header!r}")

        for row in reader:
            if len(row) < 3:
                continue
            unit, _count, pronunciation = row[0], row[1], row[2]
            for spoken, written in expand_pairs(unit, pronunciation):
                if "=>" in spoken or "=>" in written:
                    continue
                key = (spoken, written)
                if key in seen:
                    continue
                seen.add(key)
                lines_out.append(f"{spoken} => {written}")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as out:
        out.write("\n".join(lines_out))
        out.write("\n")

    print(f"Wrote {len(lines_out)} lines to {args.output}")


if __name__ == "__main__":
    main()
