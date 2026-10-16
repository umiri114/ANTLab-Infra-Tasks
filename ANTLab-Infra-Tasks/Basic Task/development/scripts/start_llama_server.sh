#!/bin/bash

# llama-server路径
LLAMA_SERVER="/home/administrator/llama.cpp/build/bin/llama-server"

# 模型路径
MODEL="/home/administrator/llama.cpp/models/qwen2.5-3b-instruct-q4_k_m.gguf"

echo "Starting llama-server..."
echo "Model: $MODEL"


$LLAMA_SERVER \
    -m "$MODEL" \
    --port 8080 \
    -ngl 999 \
    -c 4096
