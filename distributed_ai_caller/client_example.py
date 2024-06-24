# client_example.py
import time

import requests


def call_ai_api(model_name, system_prompt, user_request, image_paths=None):
    url = "http://localhost:5000/call_ai"
    payload = {
        "model_name": model_name,
        "system_prompt": system_prompt,
        "user_request": user_request,
        "image_paths": image_paths
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()  # 如果请求失败，这将抛出异常
    return response.json()["task_id"]


def get_result(task_id):
    url = f"http://localhost:5000/get_result/{task_id}"
    max_retries = 10
    retry_delay = 2

    for _ in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # 如果请求失败，这将抛出异常
            result = response.json()
            if result["status"] == "completed":
                return result["result"]
            elif result["status"] == "error":
                raise Exception(result["message"])
            time.sleep(retry_delay)
        except requests.RequestException as e:
            print(f"请求发生错误: {e}")
            time.sleep(retry_delay)

    raise TimeoutError("获取结果超时")


def main():
    try:
        # 示例1：调用OpenAI的GPT模型
        # print("调用OpenAI的GPT模型:")
        # task_id = call_ai_api(
        #     "gpt-3.5-turbo",
        #     "你是一个有用的助手。",
        #     "请用中文总结一下人工智能的主要应用领域。",
        #     image_paths=["path/to/your/image.jpg"]
        # )
        # result = get_result(task_id)
        # print(result)
        # print("\n" + "=" * 50 + "\n")

        # 示例2：调用Anthropic的Claude模型
        print("调用Anthropic的Claude模型:")
        task_id = call_ai_api(
            "claude-3-haiku-20240307",
            "你是一个专业的科技评论家。",
            "请评论一下大型语言模型对社会的潜在影响。"
        )
        task_id2 = call_ai_api(
            "claude-3-haiku-20240307",
            "你是一个专业的键政乐子人。",
            "请评论一下大型语言模型对社会的潜在影响。"
        )
        print("调用Anthropic的Claude模型的视觉任务:")
        task_id3 = call_ai_api(
            "claude-3-haiku-20240307",
            "你是一个有用的助手，能够比较图片。",
            "对比这两张图片。",
            image_paths=["path/to/first/image.jpg", "path/to/second/image.jpg"]
        )
        result = get_result(task_id)
        print(result)
        print("------------------------")
        result = get_result(task_id2)
        print(result)
        print("------------------------")
        result = get_result(task_id3)
        print(result)

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    main()