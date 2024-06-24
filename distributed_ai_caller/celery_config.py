# celery_config.py
import sys
import json
import os

import anthropic
from celery import Celery
from openai import OpenAI
from image_utils import image_to_base64

# 创建Celery应用
app = Celery('ai_tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
app.conf.broker_connection_retry_on_startup = True

# 增加更多的调试配置
app.conf.update(
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


def load_api_keys(file_path='secrets.json'):
    """
    从JSON文件中加载API密钥
    """
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建JSON文件的完整路径
    full_path = os.path.join(current_dir, file_path)

    try:
        with open(full_path, 'r') as file:
            keys = json.load(file)
        return keys
    except FileNotFoundError:
        print(f"错误: 无法找到文件 {full_path}")
        return None
    except json.JSONDecodeError:
        print(f"错误: {file_path} 不是有效的JSON文件")
        return None


# 使用示例
api_keys = load_api_keys()
if api_keys:
    pass
else:
    print("无法加载API密钥，请检查api_keys.json文件")

openai_key = api_keys['openai']['api_key']
anthropic_key = api_keys['anthropic']['api_key']
# OpenAI客户端初始化
openai_client = OpenAI()
# Anthropic客户端初始化
anthropic_client = anthropic.Anthropic(api_key=anthropic_key)


@app.task(name='ai_tasks.call_ai_api', bind=True)
def call_ai_api(self, model_name, system_prompt, user_request):
    print(f"Task {self.request.id} started: model={model_name}")
    try:
        if "gpt" in model_name.lower():
            result = call_openai_api(model_name, system_prompt, user_request)
        elif "claude" in model_name.lower():
            result = call_claude_api(model_name, system_prompt, user_request)
        else:
            raise ValueError(f"Unsupported model: {model_name}")
        print(f"任务 {self.request.id} 成功完成")
        return result
    except Exception as e:
        error_msg = f"call_ai_api 错误: {str(e)}"
        print(error_msg, file=sys.stderr)
        self.update_state(state='FAILURE', meta={'error': error_msg})
        raise


@app.task(name='ai_tasks.call_ai_api', bind=True)
def call_ai_api(self, model_name, system_prompt, user_request, image_paths=None):
    print(f"Task {self.request.id} started: model={model_name}")
    try:
        if "gpt" in model_name.lower():
            result = call_openai_api(model_name, system_prompt, user_request, image_paths)
        elif "claude" in model_name.lower():
            result = call_claude_api(model_name, system_prompt, user_request, image_paths)
        else:
            raise ValueError(f"Unsupported model: {model_name}")
        print(f"Task {self.request.id} completed successfully")
        return result
    except Exception as e:
        error_msg = f"Error in call_ai_api: {str(e)}"
        print(error_msg, file=sys.stderr)
        self.update_state(state='FAILURE', meta={'error': error_msg})
        raise

def call_openai_api(model_name, system_prompt, user_request, image_paths=None):
    print("开始调用OpenAI API")
    try:
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if image_paths:
            for image_path in image_paths:
                base64_image = image_to_base64(image_path)
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                })

        messages.append({"role": "user", "content": user_request})

        completion = openai_client.chat.completions.create(
            model=model_name,
            messages=messages
        )
        result = completion.choices[0].message.content
        print(f"OpenAI API调用完成，结果： {result}")
        return result
    except Exception as e:
        print(f"OpenAI API调用失败，结果： {str(e)}")
        raise

def call_claude_api(model_name, system_prompt, user_request, image_paths=None):
    print("开始调用Anthropic API")
    try:
        messages = []

        if image_paths:
            for i, image_path in enumerate(image_paths, 1):
                base64_image = image_to_base64(image_path)
                messages.extend([
                    {"type": "text", "text": f"Image {i}:"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image,
                        },
                    }
                ])

        messages.append({"type": "text", "text": user_request})

        message = anthropic_client.messages.create(
            model=model_name,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": messages}]
        )
        result = message.content[0].text
        print(f"Anthropic API调用完成，结果： {result}")
        return result
    except anthropic.APIError as e:
        error_msg = f"Anthropic API调用错误： {str(e)}"
        print(error_msg, file=sys.stderr)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Anthropic API调用错误： {str(e)}"
        print(error_msg, file=sys.stderr)
        raise ValueError(error_msg)


if __name__ == '__main__':
    # 当直接运行此脚本时，使用单进程模式和调试日志级别
    argv = [
        'worker',
        '--loglevel=info',
        '-P', 'solo',
    ]
    # argv = [
    #     'worker',
    #     '--loglevel=DEBUG',
    #     '-P', 'solo',
    # ]
    app.worker_main(argv)
