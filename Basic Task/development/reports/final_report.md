# ANTLab Infra 基础阶段考核报告



## 1. 基本信息

- 姓名：`[闫宇]`
- 仓库：`https://github.com/umiri114/ANTLab-Infra-Tasks`
- 分支：`master`
- 最终提交 SHA：`[待最终提交完成后填写]`
- 报告日期：2026-10-16
- 项目目录：`Basic Task/development/`

## 2. 项目目标与场景

本项目搭建面向不超过 10 人的小型团队的本地 GPU 大模型推理服务，支持通过 HTTP API 提交文本问题，并支持读取本地测试文件内容后拼接到提示词中。服务基于 llama.cpp 的 `llama-server` 和 FastAPI，配套提供请求日志、单请求基准和并发基准脚本。

当前已实现并验证的核心链路为：

```text
HTTP 客户端 / 测试脚本
  -> FastAPI API
  -> 文件内容读取与提示词拼接（可选）
  -> llama-server OpenAI-compatible completion/chat API
  -> 模型生成
  -> 返回结果并记录请求状态/延迟
```

## 3. 环境与模型

### 3.1 硬件与软件环境

| 项目 | 当前记录 |
|---|---|
| GPU | NVIDIA GeForce RTX 4060 |
| GPU 显存 | 8188 MiB（约 8 GiB） |
| CPU | 13th Gen Intel Core i9-13980HX |
| 逻辑 CPU 数 | 32 |
| WSL 可用内存 | 约 7.6 GiB |
| Swap | 约 2.0 GiB |
| 系统 | WSL2 / Ubuntu 26.04 LTS（以本机命令输出为准） |
| NVIDIA-SMI 驱动信息 | 615.65.07 |
| KMD 版本 | 616.64 |
| CUDA UMD | 13.4 |
| CUDA Toolkit | 13.3，`nvcc` 版本 V13.3.73 |
| llama.cpp commit | `aa94f2086147cd4bfbcff818ce998dffce5fcb39` |
| Python | 3.14（开发环境记录） |
| 主要 Python 依赖 | FastAPI、Uvicorn、Requests |

### 3.2 模型信息

| 项目 | 实际配置 |
|---|---|
| 模型名称 | Qwen2.5-3B-Instruct |
| 模型文件 | `qwen2.5-3b-instruct-q4_k_m.gguf` |
| 模型路径 | `/home/administrator/llama.cpp/models/qwen2.5-3b-instruct-q4_k_m.gguf` |
| 模型来源 | [Qwen2.5-3B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF) |
| 量化格式 | Q4_K_M |
| 文件大小 | 2,104,932,768 bytes |
| SHA256 | `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d` |
| 模型训练上下文长度 | 32,768 tokens（以模型元数据为准） |
| 实际服务上下文配置 | `-c 4096` |
| GPU 卸载参数 | `-ngl 999`，实际日志确认 37/37 层卸载至 GPU |



## 4. GPU 卸载与 KV 缓存实测

在 `llama-server` 启动时启用详细日志并筛选关键词，获取到以下实际输出：

```text
offloaded 37/37 layers to GPU
CUDA0 model buffer size = 1834.83 MiB
CUDA0 KV buffer size = 144.00 MiB
n_slots = 4
n_ctx_slot = 4096
kv_unified = 'true'
listening on http://127.0.0.1:8080
```

| 项目 | 实测结果 |
|---|---:|
| GPU 卸载层数 | 37/37 |
| CUDA0 模型缓冲区 | 1834.83 MiB |
| CUDA0 KV 缓存分配量 | 144.00 MiB |
| 服务槽位数 | 4 |
| 单槽位上下文参数 | 4096 |
| 统一 KV 缓存管理 | 已启用 |
| 运行时 GPU 显存快照 | 2185 MiB / 8188 MiB |

运行时 `nvidia-smi` 快照曾显示 GPU 上有 `/llama-server` 进程（PID 671），占用约 2185 MiB 显存。该快照不是峰值显存数据。模型缓冲区、KV 缓存和总显存占用是不同统计口径，不应简单相加后当作 GPU 总占用。

## 5. 系统模块与文件组织

| 模块 | 位置 | 作用 |
|---|---|---|
| FastAPI 服务 | `src/api/main.py` | 接收 API 请求、读取可选文件输入、调用 llama-server、返回结果并记录请求 |
| llama-server 启动脚本 | `scripts/start_llama_server.sh` | 启动本地 GGUF 推理服务 |
| API 启动脚本 | `scripts/start_api.sh` | 启动 FastAPI |
| API 测试 | `tests/test_api.sh` | 验证接口基本行为 |
| 单请求基准 | `tests/benchmark_single.py` | 测量单请求延迟与成功率 |
| 并发基准 | `tests/benchmark_concurrent.py` | 测试并发度 1、2、4 下的表现 |
| 请求日志 | `results/requests.jsonl` | 按行保存 API 请求记录 |
| 单请求结果 | `tests/results/single.json` | 保存单请求测试汇总 |
| 并发结果 | `tests/results/concurrent.json` | 保存并发测试汇总 |

请求日志当前记录的基础字段包括 request ID、prompt/file 信息、开始/结束时间、延迟和状态。完整的输入/输出 token 数、TTFT、TPOT、配置版本和峰值显存尚未形成统一且完整的记录链路。

## 6. 工作负载与测试方法

### 6.1 已执行测试

- 单请求基准：10 个请求。
- 并发基准：并发度 1、2、4，每种并发度 20 个请求。
- 服务健康检查：`GET /health` 返回 `{"status":"ok"}`。
- 模型接口检查：`GET /v1/models` 返回当前模型路径和元数据。
- 文件输入：已使用测试文本 `Qwen是一种大语言模型` 验证文件内容可被读取并拼接到提示词中。

### 6.2 测试限制

当前结果是已运行测试的汇总，不代表已完成正式验收所需的全部实验。每个核心配置至少三轮的重复测试尚未完成；固定的 10 项工作负载（4 个提示词、4 份办公文档、2 个源代码文件）尚无完整证据表。当前记录也没有完整覆盖输入/输出 token 数、TTFT、TPOT、缓存冷热状态、随机种子和峰值显存。

## 7. 性能结果

### 7.1 单请求基准

结果文件：`tests/results/single.json`

| 指标 | 结果 |
|---|---:|
| 请求数 | 10 |
| 成功数 | 10 |
| 失败数 | 0 |
| 成功率 | 100% |
| 平均延迟 | 0.763005 s |
| 最小延迟 | 0.380443 s |
| 最大延迟 | 1.644400 s |
| P50 延迟 | 0.601901 s |
| P95 延迟 | 1.578540 s |

该测试记录中的 `output_length` 数值约为 799–1026，但当前未核实它是字符数还是 token 数，因此不将其作为输出 token 统计。

### 7.2 并发基准

结果文件：`tests/results/concurrent.json`

| 并发度 | 请求数 | 成功数 | 成功率 | 总耗时 (s) | 吞吐 (req/s) | 平均延迟 (s) | 最小延迟 (s) | 最大延迟 (s) | P50 (s) | P95 (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 20 | 20 | 100% | 163.7470 | 0.12214 | 8.1872 | 5.4719 | 10.8087 | 8.2435 | 10.7086 |
| 2 | 20 | 20 | 100% | 91.8156 | 0.21783 | 8.8328 | 6.6586 | 12.1876 | 8.5957 | 11.1027 |
| 4 | 20 | 20 | 100% | 89.1436 | 0.22436 | 16.6254 | 7.0714 | 20.4194 | 17.1388 | 19.9161 |

### 7.3 结果解释

1. 并发度从 1 增加到 2 时，吞吐由约 0.122 req/s 上升至 0.218 req/s，增幅约 78%。
2. 并发度从 2 增加到 4 时，吞吐仅由约 0.218 req/s 上升至 0.224 req/s，增幅约 3%。
3. 并发度从 2 增加到 4 时，平均延迟从约 8.83 s 上升至约 16.63 s，说明更高并发带来了明显的请求排队或资源竞争，吞吐收益已趋于饱和。
4. 因此，在当前这一组并发测试中，并发度 2 是比并发度 4 更平衡的候选配置。但尚需多轮重复测试和一致的工作负载来确认。

单请求测试的平均延迟为约 0.763 s，而并发测试的平均延迟为约 8–17 s。由于测试工作负载和测量条件尚未证明完全一致，不能将单请求结果与并发结果直接作为优化前后对照。

### 7.4 尚未测量的指标

- TTFT（首 token 时间）
- TPOT（每输出 token 平均时间）
- token/s（需要可靠输入/输出 token 计数）
- 峰值 GPU 显存
- 输出质量的结构化评分
- 故障恢复时间及故障期间请求的结果

这些指标应在后续统一测量方法后补齐，当前不虚构数值。

## 8. 优化过程与结论

当前最有依据的性能观察来自并发度扫描：从并发 1 提升到 2 时，吞吐显著提高；继续提升到 4 时吞吐收益很小，但平均延迟和 P95 明显变差。因此，可以将“将并发控制在较合适水平，避免过度并发导致尾延迟恶化”作为后续优化方向。

目前尚无严格匹配的 baseline/optimized 两套配置、三轮重复结果和完整资源记录，因此本报告不声称已经完成经过严格验证的优化前后对照。后续应固定模型、提示词、输出上限、缓存状态和测试轮次，再比较配置变更的效果。

## 9. 输出质量、错误处理与恢复

### 9.1 已验证内容

- llama-server 启动并监听 `127.0.0.1:8080`。
- `/health` 返回 `{"status":"ok"}`。
- `/v1/models` 返回模型元数据。
- 单请求基准 10/10 成功。
- 并发度 1、2、4 的测试各 20/20 成功。
- 已验证简单文本文件可被读取并拼接到提示词。

### 9.2 未完成或缺少证据的内容

- 办公文档和代码任务的系统化输出质量评估尚未形成完整记录。
- 尚未完成服务崩溃/进程终止后的恢复演练。
- 尚无检测时间、重启时间、就绪时间、恢复总时长及在途请求处理结果的完整时间线。
- 没有独立前端页面的交付证据；当前主要通过 HTTP API 和测试脚本进行交互。

这些项目应如实列为限制，不应仅凭健康检查成功就声称故障恢复机制已通过验证。

## 10. 可复现步骤

以下命令假定仓库位于 `~/ANTLab-Infra-Tasks`，并使用本机已编译的 llama.cpp。

### 10.1 启动 llama-server

终端 A：

```bash
cd ~/ANTLab-Infra-Tasks
bash "Basic Task/development/scripts/start_llama_server.sh"
```

### 10.2 启动 FastAPI

终端 B：

```bash
cd ~/ANTLab-Infra-Tasks
source .venv/bin/activate
bash "Basic Task/development/scripts/start_api.sh"
```

启动脚本中的模型路径和二进制路径是本机绝对路径，换机器运行前需要修改。

### 10.3 检查服务

```bash
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/v1/models
```

### 10.4 运行测试

```bash
cd ~/ANTLab-Infra-Tasks
source .venv/bin/activate
bash "Basic Task/development/tests/test_api.sh"
python "Basic Task/development/tests/benchmark_single.py"
python "Basic Task/development/tests/benchmark_concurrent.py"
```

### 10.5 查看 GPU 卸载与 KV 缓存日志

停止当前 llama-server 后，可在终端直接执行以下命令查看详细日志（不保存日志文件）：

```bash
/home/administrator/llama.cpp/build/bin/llama-server \
  -m /home/administrator/llama.cpp/models/qwen2.5-3b-instruct-q4_k_m.gguf \
  --port 8080 -ngl 999 -c 4096 -v 2>&1 |
grep --line-buffered -Ei 'offload|KV buffer|KV self|CUDA0 model buffer|n_slots|n_ctx_slot|listening'
```

本次实测输出为 37/37 层卸载到 GPU、模型缓冲区 1834.83 MiB、KV 缓存 144.00 MiB、4 个槽位、单槽位上下文参数 4096。

## 11. AI 辅助与开源使用说明

开发过程中使用 AI 辅助解释构建配置、排查接口问题、整理基准测试和撰写文档。实际部署、脚本运行、GPU 日志和性能数字以本机执行结果为依据。项目使用开源 `llama.cpp`，其 commit 为 `aa94f2086147cd4bfbcff818ce998dffce5fcb39`。模型许可与原始下载来源应在最终提交前根据实际模型发布页补充。

## 12. 结论与后续改进

本项目已经建立本地 GPU 推理服务的基本链路，完成 FastAPI 调用、简单文件输入、请求日志、健康检查、单请求和多种并发度测试。GPU 日志确认模型 37/37 层卸载到 GPU，CUDA0 模型缓冲区为 1834.83 MiB，KV 缓存为 144.00 MiB。

当前数据提示并发度 2 比并发度 4 更适合作为后续调优的候选配置，因为并发度 4 的吞吐增益有限但延迟明显升高。项目仍需补齐多轮重复实验、TTFT/TPOT、峰值显存、固定办公文档/代码工作负载、前端展示和故障恢复证据。最终提交应优先保证结果可复现、数据真实和已知限制清晰。


