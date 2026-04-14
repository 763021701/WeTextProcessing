#!/usr/bin/env python3
# Run zh ITN (processor_main) on synthetic input: <prefix><pronunciation>,
# then check whether the verbalized line contains the CSV unit substring.

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def run_itn(
    binary: Path,
    tagger: Path,
    verbalizer: Path,
    text: str,
    cwd: Path,
    timeout_s: float,
) -> tuple[int, str, str]:
    """Returns (exit_code, stdout, stderr)."""
    cmd = [
        str(binary),
        "--tagger",
        str(tagger),
        "--verbalizer",
        str(verbalizer),
        "--text",
        text,
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    return proc.returncode, proc.stdout, proc.stderr


def last_verbalized_line(stdout: str) -> str:
    lines = [ln for ln in stdout.splitlines() if ln.strip() != ""]
    if not lines:
        return ""
    # processor_main prints tagged line then verbalized line
    return lines[-1].strip()


def unit_matches_output(unit: str, out: str, ignore_case: bool) -> bool:
    u = unit.strip()
    if not u:
        return False
    if ignore_case:
        return u.lower() in out.lower()
    return u in out


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "For each CSV row, run processor_main with --text <prefix><pronunciation> "
            "and check if the unit string appears in the ITN output line."
        )
    )
    p.add_argument(
        "--csv",
        type=Path,
        default=Path("raw/all_units_with_pronunciation.csv"),
        help="CSV with columns unit,count,pronunciation",
    )
    p.add_argument(
        "--binary",
        type=Path,
        default=Path("build/bin/processor_main"),
        help="Path to processor_main",
    )
    p.add_argument(
        "--tagger",
        type=Path,
        default=Path("itn/zh_itn_tagger.fst"),
        help="Tagger FST path (relative to --cwd unless absolute)",
    )
    p.add_argument(
        "--verbalizer",
        type=Path,
        default=Path("itn/zh_itn_verbalizer.fst"),
        help="Verbalizer FST path (relative to --cwd unless absolute)",
    )
    p.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help="Repo root for processor_main and relative FST paths (default: current directory)",
    )
    p.add_argument(
        "--prefix",
        default="一",
        help="Prepended to pronunciation so measures often parse (default: 一)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process at most N data rows (0 means all)",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-invocation timeout in seconds",
    )
    p.add_argument(
        "--ignore-case",
        action="store_true",
        help="Case-insensitive substring match for unit in output",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write TSV report (status, unit, pronunciation, output, exit_code)",
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only print summary counts",
    )
    args = p.parse_args()

    repo_root = args.cwd.resolve() if args.cwd is not None else Path.cwd().resolve()

    csv_path = args.csv if args.csv.is_absolute() else (repo_root / args.csv)
    csv_path = csv_path.resolve()
    if not csv_path.is_file():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 2

    binary = args.binary if args.binary.is_absolute() else (repo_root / args.binary)
    binary = binary.resolve()
    if not binary.is_file():
        print(f"ERROR: processor_main not found: {binary}", file=sys.stderr)
        return 2

    tagger = args.tagger if args.tagger.is_absolute() else (repo_root / args.tagger)
    verbalizer = args.verbalizer if args.verbalizer.is_absolute() else (repo_root / args.verbalizer)
    if not tagger.is_file():
        print(f"ERROR: tagger FST not found: {tagger}", file=sys.stderr)
        return 2
    if not verbalizer.is_file():
        print(f"ERROR: verbalizer FST not found: {verbalizer}", file=sys.stderr)
        return 2

    ok = 0
    bad = 0
    err = 0
    rows_out: list[tuple[str, str, str, str, str, str]] = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or len(header) < 3:
            print("ERROR: expected header unit,count,pronunciation", file=sys.stderr)
            return 2

        for i, row in enumerate(reader):
            if args.limit and i >= args.limit:
                break
            if len(row) < 3:
                continue
            unit, _count, pron = row[0], row[1], row[2]
            unit = unit.strip()
            pron = pron.strip()
            if not pron:
                continue

            text = f"{args.prefix}{pron}"
            code, stdout, stderr = run_itn(
                binary, tagger, verbalizer, text, repo_root, args.timeout
            )
            out_line = last_verbalized_line(stdout)
            status = "ERROR"
            if code != 0:
                err += 1
                status = "EXIT_NONZERO"
            elif unit_matches_output(unit, out_line, args.ignore_case):
                ok += 1
                status = "OK"
            else:
                bad += 1
                status = "MISS"

            rows_out.append((status, unit, pron, text, out_line, str(code)))
            if not args.quiet and status != "OK":
                print(
                    f"[{status}] unit={unit!r} pron={pron!r} input={text!r} "
                    f"exit={code} out={out_line!r}",
                    file=sys.stderr,
                )

    total = ok + bad + err
    print(
        f"Summary: OK={ok} MISS={bad} ERROR={err} TOTAL={total} "
        f"(prefix={args.prefix!r} csv={csv_path})"
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as wf:
            w = csv.writer(wf, delimiter="\t", lineterminator="\n")
            w.writerow(["status", "unit", "pronunciation", "input_text", "itn_output", "exit_code"])
            w.writerows(rows_out)

    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
