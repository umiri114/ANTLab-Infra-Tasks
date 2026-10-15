#!/bin/bash

curl -X POST \
http://localhost:8000/chat \
-H "Content-Type: application/json" \
-d '{"message":"介绍一下你的功能"}'
