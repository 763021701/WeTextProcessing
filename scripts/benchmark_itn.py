#!/usr/bin/env python3
"""One-shot ITN timing: Python vs C++ on a fixed long sentence.

  python3 scripts/benchmark_itn.py
  python3 scripts/benchmark_itn.py --processor-main ./build/bin/processor_main
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

TEXT = (
    "组织样本中激素含量为五纳摩尔每克，血清醛固酮浓度为十纳摩尔每分升，酶反应速率为十二纳摩尔每分钟每十的六次方细胞，受体结合量为零点五纳摩尔每十的七次方，血小板激活指标为二纳摩尔每十的九次方血小板，血浆皮质醇水平为五百纳摩尔每升，药物在组织中的分布为零点一纳摩尔每毫克，脑脊液蛋白浓度为一纳摩尔每毫升，代谢产物生成速率为零点零五纳摩尔每毫升每小时，尿铵排泄量为三十微摩尔每两小时，尿钙总量为五点零微摩尔每二十四小时，肝脏药物浓度为二十微摩尔每克，尿白蛋白排泄率为三十微摩尔每克肌酐，儿童用药剂量为五十微摩尔每公斤，维持剂量为零点一微摩尔每公斤每天，血浆渗透压调节为二八零一毫渗量每公斤水，血清渗透压为二九零一毫渗量每升，抗毒素效价为五十治疗单位每毫升，尿液总渗透压为零点八渗摩尔每升，血浆渗透压摩尔浓度为零点三渗透压摩尔每千克，感染指标显示白细胞计数为五千白细胞每微升，空气中污染物浓度为零点五百万分之一，头发汞含量为五十皮克每克，新生儿筛查值为十皮克每分升，以及环境水样检测值为五皮克每升。"
)


def find_repo_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / "pyproject.toml").is_file() and (p / "itn").is_dir():
            return p
    return None


def default_processor_main(repo: Path) -> Path | None:
    for c in (
        repo / "build" / "bin" / "processor_main",
        repo / "runtime" / "build" / "bin" / "processor_main",
    ):
        if c.is_file() and os.access(c, os.X_OK):
            return c
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="One-shot Chinese ITN: Python vs C++ timing.")
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="WeTextProcessing root (default: search from cwd)",
    )
    parser.add_argument("--cache-dir", type=Path, default=None, help="Directory with zh_itn_*.fst")
    parser.add_argument("--processor-main", type=Path, default=None, help="Path to processor_main")
    parser.add_argument("--skip-cpp", action="store_true")
    args = parser.parse_args()

    start = Path(args.repo).resolve() if args.repo else Path.cwd().resolve()
    repo = find_repo_root(start)
    if repo is None:
        print(
            "ERROR: repo not found (need pyproject.toml + itn/). Use --repo.",
            file=sys.stderr,
        )
        return 1

    cache_dir = (args.cache_dir or (repo / "itn")).resolve()
    tagger = cache_dir / "zh_itn_tagger.fst"
    verbalizer = cache_dir / "zh_itn_verbalizer.fst"
    if not tagger.is_file() or not verbalizer.is_file():
        print(
            f"ERROR: missing FST in {cache_dir}. "
            "Run: python -m itn --text test --overwrite_cache",
            file=sys.stderr,
        )
        return 1

    os.chdir(repo)
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    from itn.chinese.inverse_normalizer import InverseNormalizer

    print(f"Input length: {len(TEXT)} chars\n")

    t0 = time.perf_counter()
    model = InverseNormalizer(cache_dir=str(cache_dir), overwrite_cache=False)
    out_py = model.normalize(TEXT)
    t_py = time.perf_counter() - t0
    print(f"Python: {t_py * 1000:.2f} ms (load FST + one normalize)")
    print(out_py)
    print()

    if args.skip_cpp:
        return 0

    exe = args.processor_main
    if exe is not None:
        exe = Path(exe).resolve()
    else:
        exe = default_processor_main(repo)

    if exe is None or not exe.is_file():
        print(
            "ERROR: processor_main not found. Build:\n"
            "  cmake -B build -S runtime -DCMAKE_BUILD_TYPE=Release && cmake --build build -j\n"
            "Or pass --processor-main",
            file=sys.stderr,
        )
        return 1

    t0 = time.perf_counter()
    r = subprocess.run(
        [
            str(exe),
            "--tagger",
            str(tagger),
            "--verbalizer",
            str(verbalizer),
            "--text",
            TEXT,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    t_cpp = time.perf_counter() - t0

    if r.returncode != 0:
        print(f"ERROR: processor_main failed: {r.stderr or r.stdout}", file=sys.stderr)
        return 1

    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    out_cpp = lines[1] if len(lines) >= 2 else ""

    print(f"C++:    {t_cpp * 1000:.2f} ms (process start + load FST + one normalize)")
    print(out_cpp)
    print()

    if out_py != out_cpp:
        print("NOTE: Python and C++ outputs differ (check rules/FST versions).", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
