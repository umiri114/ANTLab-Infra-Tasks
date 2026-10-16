# Source Code — 核心源码说明

## 1. 目录用途

本目录存放 ANTLab 本地大模型推理服务的核心应用代码，负责接收用户请求、处理输入文件、调用 llama.cpp 推理服务，并记录请求运行信息。

## 2. 目录结构

```text
src/
└── api/
    └── main.py
```

| 文件 | 职责 |
|---|---|
| `api/main.py` | 基于 FastAPI 实现 HTTP 接口、输入处理、模型服务调用、响应返回及请求日志记录 |

## 3. 核心功能

### 3.1 HTTP API

应用通过 FastAPI 提供 HTTP 接口，包括：

- `GET /`：检查 API 服务是否正常运行。
- `POST /chat`：接收文本请求，可选关联输入文件，并调用本地大模型服务生成回答。

### 3.2 输入文件处理

当请求提供 `file_path` 时，应用读取对应文件内容，并将其与用户的任务提示组合后发送给模型。

该机制可用于文档总结、信息提取等任务。实际支持的文件类型与读取方式以当前实现为准。

### 3.3 模型服务调用

应用通过 HTTP 请求调用 llama.cpp 的 OpenAI 兼容聊天补全接口：

`http://localhost:8080/v1/chat/completions`

当前请求代码显式设置生成温度 `temperature=0.7`，并根据请求中的 `stream` 字段传递流式响应设置。

### 3.4 请求日志

应用将请求运行信息写入 `results/requests.jsonl`，记录字段以实际实现为准，可用于分析请求状态、处理耗时及输入来源。

### 3.5 请求标识与追踪

请求可以携带 `prompt_id` 和 `run_id` 等标识，用于关联测试提示和实验运行。具体哪些标识被写入日志、返回结果或传递给模型，以当前代码实现为准。

## 4. 请求处理流程

```text
客户端发送请求
       |
       v
FastAPI 接收请求
       |
       v
读取可选输入文件
       |
       v
组合提示词与文件内容
       |
       v
调用 llama-server
       |
       v
接收模型响应
       |
       v
记录请求运行信息
       |
       v
返回 HTTP 响应
```

## 5. 运行方式

请先启动 llama-server，再启动 FastAPI 应用。

在项目的 `Basic Task/development/` 目录下执行：

```bash
bash scripts/start_llama_server.sh
```

在另一个终端执行：

```bash
bash scripts/start_api.sh
```

启动脚本中的路径、端口和运行参数以当前脚本内容为准。

## 6. 测试方式

接口功能测试脚本位于 `tests/test_api.sh`，性能测试脚本位于：

- `tests/benchmark_single.py`
- `tests/benchmark_concurrent.py`

测试生成的汇总结果保存在 `tests/results/`，逐请求日志保存在 `results/requests.jsonl`。

## 7. 实现范围与限制

当前源码实现了基本的 HTTP 请求处理、输入文件读取、本地模型调用和请求日志记录。更完善的并发调度、文件格式支持、异常恢复和运行监控，可根据测试结果继续扩展。

本文件仅说明核心源码的职责；实际行为以当前版本代码和测试结果为准。

