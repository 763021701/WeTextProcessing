---
name: wetext-cpp-runtime-build
description: Builds the WeTextProcessing C++ runtime (OpenFst-based processor_main) on Linux, handles OpenFst FetchContent failures via local tarball, and documents FST paths and runtime limits. Use when compiling runtime/, processor_main, OpenFst integration, or comparing Python weitn vs C++ ITN/TN.
---

# WeTextProcessing C++ Runtime Build

## Scope

- **In-repo**: `runtime/` (CMake + OpenFst via FetchContent + `processor_main`).
- **Not** `pip install` / `weitn` / `wetn` — those are Python entry points.

## Prerequisites (Linux)

- `build-essential`, `cmake` (≥3.14), `git`.
- Network access for the **default** OpenFst download, **or** a local tarball (see below).

## Configure and build

**Option A — build directory at repo root** (matches root `README.md`):

```bash
cd /path/to/WeTextProcessing
cmake -B build -S runtime -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

Binary: `build/bin/processor_main` (confirm with `find build -name processor_main`).

**Option B — build inside `runtime/`** (matches `runtime/README.md`):

```bash
cd /path/to/WeTextProcessing/runtime
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

Binary: `runtime/build/bin/processor_main` (or `find build -name processor_main`).

## OpenFst download fails (CMake error on `openfst-populate`)

FetchContent pulls OpenFst from GitHub (`runtime/cmake/openfst.cmake`). If download fails (network, TLS, firewall):

1. Obtain the **same** archive as upstream: tag `win/1.7.2.1` from `kkm000/openfst` (filename like `1.7.2.1.tar.gz`).
2. In `runtime/cmake/openfst.cmake`, set `FetchContent_Declare(openfst ...)` **`URL`** to a local file URI (three slashes for absolute path):

   `file:///absolute/path/to/1.7.2.1.tar.gz`

3. Keep **`URL_HASH`** unchanged unless the file differs (then recompute `sha256sum` and update hash).
4. Remove stale Fetch cache before re-running CMake: delete `runtime/fc_base-*` (and the failed `build` tree if needed).

Optional: `sudo apt-get install ca-certificates` and retry online fetch.

## Run `processor_main`

Requires **real paths** — not placeholder `/path/to/WeTextProcessing`.

- **ITN (Chinese)**: `tagger` path string must contain **`zh_itn_`** (e.g. `zh_itn_tagger.fst`). Same for verbalizer.
- **TN**: paths must contain `zh_tn_`, `en_tn_`, or `ja_tn_` as implemented in `runtime/processor/wetext_processor.cc`.
- **Japanese ITN** (`ja_itn_`) is **not** wired in that C++ constructor; use Python for JA ITN.

Generate FSTs with Python if missing:

```bash
cd /path/to/WeTextProcessing
python -m itn --text test --overwrite_cache   # zh ITN under itn/
python -m tn --text test --overwrite_cache    # tn under tn/
```

Example:

```bash
./build/bin/processor_main \
  --tagger "$PWD/itn/zh_itn_tagger.fst" \
  --verbalizer "$PWD/itn/zh_itn_verbalizer.fst" \
  --text "二点五平方电线"
```

Output: first line = tagger output, second line = normalized text.

## Quick verification

```bash
./build/bin/processor_main --tagger ... --verbalizer ... --text "测"
```

If FST paths are wrong, OpenFst logs read errors; avoid reusing doc placeholders literally.

## Optional tests

```bash
cmake -B build -S runtime -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build -j"$(nproc)"
ctest --test-dir build
```

## Reference

- `runtime/README.md` — build and wget examples for released FSTs.
- `runtime/cmake/openfst.cmake` — OpenFst `URL` / `URL_HASH` / patch step.
