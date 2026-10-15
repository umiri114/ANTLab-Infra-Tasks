from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

import requests
import uuid
import time
import json
import os


app = FastAPI(
    title="ANTLab LLM API",
    description="FastAPI wrapper for llama-server",
    version="1.0"
)


# llama-server地址
LLAMA_SERVER_URL = "http://localhost:8080/v1/chat/completions"


# 日志保存位置
LOG_FILE = "results/requests.jsonl"


# 请求格式
class ChatRequest(BaseModel):
    message: str

    file_path: str | None = None

    prompt_id:str | None = None

    run_id:str | None = None

    stream: bool = False



def save_log(data):

    os.makedirs(
        os.path.dirname(LOG_FILE),
        exist_ok=True
    )

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                data,
                ensure_ascii=False
            )
            + "\n"
        )



@app.get("/")
def root():
    return {
        "status": "running",
        "service": "ANTLab LLM API"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())

    start_time = time.time()


    # ==========================
    # 处理文件输入
    # ==========================

    prompt = request.message


    if request.file_path:

        try:

            with open(
                request.file_path,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read()


            prompt = f"""

文件内容：

{content}


用户任务：

{request.message}
"""




        except Exception as e:

            return {
                "error": "file read failed",
                "detail": str(e)
            }



    payload = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,

	"stream":request.stream
    }


    try:



        response = requests.post(
            LLAMA_SERVER_URL,
            json=payload,
            timeout=120,
	    stream=request.stream
        )

        #print("llama response status:", response.status_code)
        #print("llama response:", response.text[:500])

        #return response.json()



        # ==========================
        # 流式输出
        # ==========================

        if request.stream:


            def generate():

                for chunk in response.iter_lines():

                    if chunk:

                        yield chunk + b"\n"



            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )



        result=response.json()



        end_time=time.time()


        # 保存请求记录

        save_log({

            "run_id":request.run_id,

            "request_id":request_id,

            "prompt":request.message,

            "prompt_id":request.prompt_id,

            "file":request.file_path,

            "start":start_time,

            "end":end_time,

            "latency":end_time-start_time,

            "status":"success"

        })

        result["request_id"] = request_id

        result["latency"] = end_time - start_time


        return result




    except Exception as e:
        save_log({


            "request_id":request_id,

            "status":"failed",

            "error": str(e)

        })

        return {

            "error":str(e)

        }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "qwen2.5-3b-instruct-q4_k_m"
    }

