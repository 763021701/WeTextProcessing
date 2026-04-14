# 中文逆文本化（ITN）命令行与运行时说明

面向本仓库源码环境，说明 Python CLI、C++ `processor_main`、性能对比脚本，以及 FST 缓存位置。

## 1. Python 逆文本化（`itn/main.py`）

CLI 入口在 `itn/main.py` 的 `main()`。从仓库根目录执行（需已安装依赖，或将仓库根加入 `PYTHONPATH`）：

```bash
cd /path/to/WeTextProcessing
python -m itn --text "二点五平方电线"
```

常用参数：


| 参数                           | 说明                         |
| ---------------------------- | -------------------------- |
| `--text`                     | 单行输入                       |
| `--file`                     | 按行读取文件                     |
| `--cache_dir`                | 存放 `*.fst` 的目录（默认见下文第 4 节） |
| `--overwrite_cache`          | 强制重新构图                     |
| `--language`                 | `zh`（默认）或 `ja`             |
| `--enable_standalone_number` | 默认 `True`：如「一百」→ `100`     |
| `--enable_0_to_9`            | 默认 `True`                 |
| `--enable_million`           | 默认 `False`                 |


安装为可编辑包后，也可用控制台入口 `weitn`（与 `python -m itn` 等价，见 `pyproject.toml`）。

## 2. C++ `processor_main`（`build/bin/processor_main`）

在仓库根目录编译后，可执行文件一般为 `build/bin/processor_main`（若在 `runtime/` 下单独建目录，则可能是 `runtime/build/bin/processor_main`）。

**编译**：可用 Cursor Skill [wetext-cpp-runtime-build](.cursor/skills/wetext-cpp-runtime-build/SKILL.md)

**运行**（中文 ITN 需传入含 `zh_itn_` 的 tagger/verbalizer 路径）：

```bash
./build/bin/processor_main \
  --tagger "$PWD/itn/zh_itn_tagger.fst" \
  --verbalizer "$PWD/itn/zh_itn_verbalizer.fst" \
  --text "五纳摩尔每克"
```

输出两行：第一行为 tagger 结果，第二行为归一化后的文本。

## 3. Python 与 C++ 耗时对比（`scripts/benchmark_itn.py`）

在同一段固定长句上，分别测「Python：加载 FST + 一次 normalize」与「C++：进程启动 + 加载 FST + 一次 normalize」的耗时。

```bash
cd /path/to/WeTextProcessing
python3 scripts/benchmark_itn.py
python3 scripts/benchmark_itn.py --processor-main ./build/bin/processor_main
```

可选：`--repo` 指定仓库根、`--cache-dir` 指定 FST 目录、`--skip-cpp` 只跑 Python。

## 4. FST 图缓存位置（`zh_itn_tagger.fst` / `zh_itn_verbalizer.fst`）

默认与 `InverseNormalizer` 未指定 `cache_dir` 时的行为一致：文件生成在仓库下的 `**itn/**` 目录：

- `itn/zh_itn_tagger.fst`
- `itn/zh_itn_verbalizer.fst`

若使用 `python -m itn --cache_dir /其他/路径`，则上述两个文件会写到该目录。首次使用或改规则后需要重新构图时，加上 `--overwrite_cache`。

## 5. 量测用例测试（`itn/chinese/test/data/measure.txt`）

量测类行用例定义在 `itn/chinese/test/data/measure.txt`（`口语 => 书面` 格式），由 `itn/chinese/test/normalizer_test.py` 与其它 `data/*.txt` 一并加载。在仓库根目录执行：

```bash
cd /path/to/WeTextProcessing
pytest itn/chinese/test/normalizer_test.py -v
```

该命令会跑完整套中文 ITN 归一化单测（含 measure 及 cardinal、date 等）；修改 `measure.txt` 或规则后可用同一命令回归。