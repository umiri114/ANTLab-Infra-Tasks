# Scripts — 服务启动脚本说明

## 1. 目录用途

本目录存放本地大模型推理服务及其 API 应用的启动脚本，用于简化开发、测试和实验时的服务启动流程。

当前启动流程由两个服务组成：

1. `llama-server`：基于 llama.cpp 加载 GGUF 模型并提供推理接口。
2. FastAPI 应用：接收客户端请求、处理输入文件、调用模型服务并返回响应。

## 2. 目录结构

```text
scripts/
├── README.md
├── start_llama_server.sh
└── start_api.sh
```

| 文件 | 用途 |
|---|---|
| `start_llama_server.sh` | 启动 llama.cpp 推理服务 |
| `start_api.sh` | 启动 FastAPI HTTP API 服务 |

## 3. 启动脚本说明

### 3.1 启动 llama-server

脚本：`start_llama_server.sh`

该脚本负责启动 llama.cpp 的 `llama-server`，加载本地 GGUF 模型，并开放供 API 应用调用的推理接口。

当前脚本配置包括：

| 参数 | 当前设置 | 说明 |
|---|---|---|
| 模型路径 | `~/llama.cpp/models/qwen2.5-3b-instruct-q4_k_m.gguf` 对应的绝对路径 | 指定加载的 GGUF 模型 |
| 服务端口 | `8080` | 模型推理服务监听端口 |
| GPU 层参数 | `-ngl 999` | 请求尽可能将模型层卸载到 GPU |
| 上下文容量 | `4096` | 设置上下文容量参数 |

`-ngl 999` 表示请求最大程度进行 GPU 层卸载，不代表实际卸载层数一定为 999。实际 GPU 卸载情况应以 `llama-server` 启动日志为准。

启动命令：

```bash
bash scripts/start_llama_server.sh
```

启动后，可观察终端日志确认模型是否成功加载以及服务是否正常启动。模型服务默认供本机 API 应用通过 `http://localhost:8080` 访问。

### 3.2 启动 FastAPI

脚本：`start_api.sh`

该脚本负责启动 FastAPI 应用，为客户端提供 HTTP API，并通过模型服务完成文本生成请求。

启动命令：

```bash
bash scripts/start_api.sh
```

API 服务默认监听 `8000` 端口，接口包括：

- `GET /`：检查 API 服务状态。
- `POST /chat`：提交文本请求，可选关联输入文件，并获取模型响应。

实际 Python 解释器、应用入口、监听地址和端口以当前脚本内容为准。

## 4. 服务启动顺序

建议先启动模型服务，再启动 API 服务。

```text
启动 start_llama_server.sh
            |
            v
模型加载并启动推理接口
            |
            v
启动 start_api.sh
            |
            v
FastAPI 开始监听请求
            |
            v
客户端通过 API 发送请求
```

两个服务建议分别在独立终端运行，以便观察各自日志及定位启动错误。

## 5. 启动前检查

启动前请确认：

1. llama.cpp 已编译生成可用的 `llama-server`。
2. 模型文件存在，且脚本中的模型路径正确。
3. Python 虚拟环境已安装项目依赖。
4. `8080` 和 `8000` 端口没有被其他进程占用。
5. 当前工作环境能够访问配置的模型服务地址。

如需更换模型或调整上下文容量、GPU 层参数，应修改 `start_llama_server.sh` 中对应的参数，并同步更新 `configs/` 中的配置记录。

## 6. 与项目其他目录的关系

- `src/api/`：保存 FastAPI 应用源码。
- `configs/`：保存模型、服务和测试配置记录。
- `tests/`：保存接口测试和性能基准测试脚本。
- `results/`：保存逐请求运行日志。
- `reports/`：保存最终实验报告。

启动脚本负责启动服务；应用的实际处理逻辑由源码实现，性能数据则由测试脚本生成。

## 7. 当前范围

本目录提供基础服务启动能力，便于重复执行模型服务与 API 应用的启动操作。

服务故障恢复、自动重启、进程监控等能力应以实际实现和测试结果为准，不因存在启动脚本就视为已经完成。
