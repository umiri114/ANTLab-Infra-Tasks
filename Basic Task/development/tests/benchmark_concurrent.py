
import json
import math
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

URL = "http://localhost:8000/chat"


BASE_DIR = Path(__file__).resolve().parents[1]


INPUT_FILE = (
    BASE_DIR.parent
    / "提示词与输入文档"
    / "输入文档"
    / "办公输入01-项目会议与进度资料.md"
)


REQUEST_DATA = {
    
    "message": "请总结这个文件内容，提取项目进展、问题和下一步计划",
    "file_path": str(INPUT_FILE.resolve()),
    "prompt_id": "office-summary-01",
    "run_id": "baseline-c2-run01",
    "stream": False


}

TOTAL_REQUESTS = 20
CONCURRENCY_LEVELS = [1, 2, 4]

BASE_DIR = Path(__file__).resolve().parents[1]
RESULT_FILE = BASE_DIR / "tests" / "results" / "concurrent.json"


def percentile(values, p):
    """使用 nearest-rank 方法计算百分位数。"""
    values = sorted(values)
    index = max(0, math.ceil(p * len(values)) - 1)
    return values[index]


def run_once(request_id):
    start = time.perf_counter()

    try:
        response = requests.post(
            URL,
            json=REQUEST_DATA,
            timeout=180
        )
        latency = time.perf_counter() - start


        error = None
        success = response.status_code == 200

        try:
            data = response.json()

            if isinstance(data, dict):
                if data.get("error"):
                    success = False
                    error = str(data["error"])
                elif data.get("status") == "error":
                    success = False
                    error = str(data)
        except ValueError:
            data = None


        return {
            "request_id": request_id,
            "status": response.status_code,
            "latency": latency,
            "output_length": len(response.text),
            "error": None
        }

    except requests.RequestException as exc:
        latency = time.perf_counter() - start

        return {
            "request_id": request_id,
            "status": 0,
            "latency": latency,
            "output_length": 0,
            "error": str(exc)
        }


def run_test(concurrency):
    results = []
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(run_once, i + 1)
            for i in range(TOTAL_REQUESTS)
        ]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            print(
                f"[并发 {concurrency}] "
                f"完成 {len(results)}/{TOTAL_REQUESTS}, "
                f"status={result['status']}, "
                f"latency={result['latency']:.3f}s"
            )

    elapsed = time.perf_counter() - start

    latencies = [r["latency"] for r in results]
    success_count = sum(
        1 for r in results if r["status"] == 200
    )

    summary = {
        "concurrency": concurrency,
        "total_requests": TOTAL_REQUESTS,
        "success_count": success_count,
        "failure_count": TOTAL_REQUESTS - success_count,
        "success_rate": success_count / TOTAL_REQUESTS,
        "total_time": elapsed,
        "throughput_rps": TOTAL_REQUESTS / elapsed,
        "avg_latency": statistics.mean(latencies),
        "min_latency": min(latencies),
        "max_latency": max(latencies),
        "p50_latency": percentile(latencies, 0.50),
        "p95_latency": percentile(latencies, 0.95),
        "results": sorted(
            results, key=lambda r: r["request_id"]
        )
    }

    return summary


def main():
    all_results = []

    # 预热请求，不计入正式测试
    print("正在预热接口...")
    warmup = run_once(0)

    if warmup["status"] != 200:
        print("预热失败，请检查 FastAPI 服务是否正常。")
        print(warmup)
        return

    print("预热成功，开始并发测试。")

    for concurrency in CONCURRENCY_LEVELS:
        print(f"\n开始测试并发数：{concurrency}")
        summary = run_test(concurrency)
        all_results.append(summary)

        print(
            f"成功率：{summary['success_rate']:.1%}, "
            f"平均延迟：{summary['avg_latency']:.3f}s, "
            f"P95：{summary['p95_latency']:.3f}s, "
            f"吞吐量：{summary['throughput_rps']:.2f} req/s"
        )

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with RESULT_FILE.open("w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n测试完成，结果已保存至：{RESULT_FILE}")


if __name__ == "__main__":
    main()
