import json
import time
import requests
import os
import threading
from queue import Queue

def call_ai_api(model_name, system_prompt, user_request, image_paths=None):
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

def evlaulateTask2(file_path, answer):
    try:
        extract_prompt = """You are tasked with extracting student answers from an image of a worksheet or test paper. The image will contain a grid of numbered questions with corresponding answers or values.
Follow these steps to extract the information and format it as a JSON string:
1. Examine the image carefully, noting that it contains a grid of numbered items from 1 to 12.
2. For each numbered item, identify the corresponding answer or value written next to or below it.
3. Create a JSON object where:
- The keys are the question numbers as strings (e.g., "1", "2", "3", etc.)
- The values are the corresponding answers as strings
4. If an answer is blank or not visible, use an empty string as the value.
5. For answers that contain mathematical symbols or special characters:
- Use "pi" for π
- Use "sqrt" for √
- Represent fractions as they appear (e.g., "24/2")
- Include parentheses, commas, and brackets as they appear
6. Ensure that all 12 items are included in the JSON object, even if some are blank.
7. Format the JSON object as a string, with each key-value pair on a new line for readability.
Your output should be a valid JSON string.
Remember to:
- Include all visible characters, including brackets, parentheses, and special symbols.
- Use the exact formatting and spacing as shown in the image.
- Double-check that your JSON string is valid and includes all 12 items.
Provide only the JSON string as your output, without any additional explanation or commentary."""

        ExtractedReply = call_ai_api(
            "claude-3-5-sonnet-20240620",
            extract_prompt,
            "Student's answer submitted!",
            image_paths=[file_path]
        )
        tExtractedReply = get_result(ExtractedReply)

        compare_prompt = """You are tasked with evaluating the correctness of student answers by comparing extracted answers to the correct answers. Both sets of answers are provided in JSON format.

Follow these steps to evaluate the answers and format the results as a JSON string:

1. Parse both JSON strings to access the extracted and correct answers.

2. For each question number (1 through 12):
a. Compare the extracted answer to the correct answer.
b. Determine if the extracted answer is correct, incorrect, or requires review.

3. Create a new JSON object where:
- The keys are the question numbers as strings (e.g., "1", "2", "3", etc.)
- The values are the evaluation results as strings: "correct", "incorrect", or "review_required"

4. Use the following criteria for evaluation:
- If the extracted answer and correct answer are exactly the same (including spacing and formatting), mark it as "correct".
- If the extracted answer is clearly different from the correct answer, mark it as "incorrect".
- If the extracted answer is equivalent in value but formatted differently, mark it as "correct".
- if the extracted answer is blank, mark it as "review_required".

5. Format the evaluation results as a JSON string, with each key-value pair on a new line for readability.

Your output should be a valid JSON string containing the evaluation results.
Additional guidelines:
- Be strict in your evaluation. If there's any doubt about the correctness, use "review_required".
- For fractions, ensure that they are equivalent even if not reduced (e.g., "24/2" is correct for "12").
- For square roots, accept both "sqrt" and "√" symbols.
- For pi, accept both "pi" and "π" symbols.
- Ignore minor spacing differences, especially in coordinate pairs or intervals.
- If either the extracted answer or the correct answer is missing or blank for a question, mark it as "blanked".

Provide only the JSON string as your output, without any additional explanation or commentary."""

        CompareOutput = call_ai_api(
            "claude-3-haiku-20240307",
            compare_prompt,
            f"Student answer: {tExtractedReply}\nCorrect answer: {answer}",
        )
        return get_result(CompareOutput)
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def worker(queue, answer):
    while True:
        file_path = queue.get()
        if file_path is None:
            break
        print(f"Processing: {file_path}")
        result = evlaulateTask2(file_path, answer)
        if result:
            root = os.path.dirname(file_path)
            with open(os.path.join(root, "result.json"), 'w') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
        queue.task_done()

def main():
    answer = """{
    "1": "1-2i",
    "2": "4",
    "3": "(2,3)",
    "4": "3",
    "5": "24",
    "6": "60°",
    "7": "4",
    "8": "2/5",
    "9": "5",
    "10": "[0,6]",
    "11": "(-√2,√2)",
    "12": "-1/(4e)"
    }"""

    file_queue = Queue()

    # 创建两个工作线程
    threads = []
    for _ in range(3):
        t = threading.Thread(target=worker, args=(file_queue, answer))
        t.start()
        threads.append(t)

    # 遍历./output/下的所有文件夹中的corrected_column_2.jpg文件
    for root, dirs, files in os.walk("./output/"):
        for file in files:
            if file == "corrected_column_2.jpg":
                file_queue.put(os.path.join(root, file))

    # 等待所有任务完成
    file_queue.join()

    # 停止工作线程
    for _ in range(3):
        file_queue.put(None)
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()