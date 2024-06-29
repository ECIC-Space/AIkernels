import json
import time
import requests
import os
import threading
from queue import Queue

def call_ai_api(model_name, system_prompt, user_request, image_paths):
    url = "http://localhost:5000/call_ai"
    payload = {
        "model_name": model_name,
        "system_prompt": system_prompt,
        "user_request": user_request,
        "image_paths": image_paths
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["task_id"]

def get_result(task_id):
    url = f"http://localhost:5000/get_result/{task_id}"
    max_retries = 10
    retry_delay = 2

    for _ in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
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

def evlaulateTask1(file_path):
    try:
        extract_prompt = """You are tasked with extracting a student's ID number from a part of an answer sheet.

Follow these steps to extract the information and format it as a JSON string:

1.      Find the 6-digits ID (started with 220) below "考号" label;
2.      Create a JSON object where:
- The key is "student_id"
- The value is a string representing the complete student ID number
3.      Format the JSON object as a string.

Provide only the JSON string as your output, without any additional explanation or commentary."""
        print(file_path)
        ExtractedReply = call_ai_api(
            "claude-3-5-sonnet-20240620",
            extract_prompt,
            "Image has been received!",
            image_paths=[file_path]
        )
        tExtractedReply = get_result(ExtractedReply)

        return tExtractedReply
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def worker(queue):
    while True:
        file_path = queue.get()
        if file_path is None:
            break
        print(f"Processing: {file_path}")
        result = evlaulateTask1(file_path)
        if result:
            root = os.path.dirname(file_path)
            print(f"Saving result to {root}/id.json")
            with open(os.path.join(root, "id.json"), 'w') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
        queue.task_done()

def main():
    file_queue = Queue()
    # 创建两个工作线程
    threads = []
    for _ in range(2):
        t = threading.Thread(target=worker, args=(file_queue,))
        t.start()
        threads.append(t)

    # 获取当前脚本的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建输出文件夹的绝对路径
    output_dir = os.path.join(script_dir, "output")

    # 遍历output文件夹下的所有文件夹中的corrected_column_1.jpg文件
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file == "corrected_column_1.jpg":
                file_path = os.path.join(root, file)
                file_queue.put(os.path.abspath(file_path))  # 使用绝对路径

    # 等待所有任务完成
    file_queue.join()

    # 停止工作线程
    for _ in range(2):
        file_queue.put(None)
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()