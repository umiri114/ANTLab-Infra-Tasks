import requests
import time
import json
import statistics


URL = "http://localhost:8000/chat"


REQUEST_DATA = {

    "prompt":
    "办公输入01-项目会议与进度资料.md",

    "message":
    "请总结这个文件内容，提取项目进展、问题和下一步计划"

}


def run_once():

    start = time.time()


    response = requests.post(
        URL,
        json=REQUEST_DATA
    )


    end = time.time()


    latency = end - start


    return {

        "status":
        response.status_code,


        "latency":
        latency,


        "output_length":
        len(response.text)

    }



def main():


    results=[]


    # 测试10次

    for i in range(10):

        print(
            f"Running {i+1}/10"
        )

        result = run_once()

        results.append(result)



    latency_list=[

        r["latency"]

        for r in results

    ]


    sorted_latencies = sorted(latency_list)

    success_count = sum(
        1 for r in results
        if r["status"] == 200
    )



    summary={

        "success_count":
        success_count,


        "success_rate":
        success_count / len(results),


        "requests":
        10,


        "avg_latency":
        statistics.mean(latency_list),


        "min_latency":
        min(latency_list),


        "max_latency":
        max(latency_list),


        "p50_latency":
        statistics.median(latency_list),


        "p95_latency": sorted_latencies[
        max(0, int(0.95 * len(sorted_latencies)) - 1)

        ],


        "results":
        results

    }



    with open(
        "tests/results/single.json",
        "w"
    ) as f:

        json.dump(
            summary,
            f,
            indent=4
        )


    print(summary)



if __name__=="__main__":

    main()
