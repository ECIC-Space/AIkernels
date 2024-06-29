import sys
import json
import os
import logging
from celery import Celery, states
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.serialization import UnpickleableExceptionWrapper

import anthropic
from openai import OpenAI
from image_utils import image_to_base64

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Celery application
app = Celery('ai_tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
app.conf.update(
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
)

def load_api_keys(file_path='secrets.json'):
    """Load API keys from a JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_path)

    try:
        with open(full_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Error: Cannot find file {full_path}")
    except json.JSONDecodeError:
        logger.error(f"Error: {file_path} is not a valid JSON file")
    return None

# Load API keys
api_keys = load_api_keys()
if not api_keys:
    logger.error("Failed to load API keys. Please check the secrets.json file.")
    sys.exit(1)

# Initialize API clients
openai_client = OpenAI(api_key=api_keys['openai']['api_key'])
anthropic_client = anthropic.Anthropic(api_key=api_keys['anthropic']['api_key'])

def safe_result(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'type': type(e).__name__
            }
    return wrapper

@app.task(name='ai_tasks.call_ai_api', bind=True, throws=(ValueError, SoftTimeLimitExceeded))
@safe_result
def call_ai_api(self, model_name, system_prompt, user_request):
    logger.info(f"Task {self.request.id} started: model={model_name}")
    if "gpt" in model_name.lower():
        result = call_openai_api(model_name, system_prompt, user_request)
    elif "claude" in model_name.lower():
        result = call_claude_api(model_name, system_prompt, user_request)
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    logger.info(f"Task {self.request.id} completed successfully")
    return {'status': 'success', 'result': result}

@app.task(name='ai_tasks.call_ai_api_img', bind=True, throws=(ValueError, SoftTimeLimitExceeded))
@safe_result
def call_ai_api_img(self, model_name, system_prompt, user_request, image_paths=None):
    logger.info(f"Task {self.request.id} started: model={model_name}")
    if "gpt" in model_name.lower():
        result = call_openai_api_img(model_name, system_prompt, user_request, image_paths)
    elif "claude" in model_name.lower():
        result = call_claude_api_img(model_name, system_prompt, user_request, image_paths)
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    logger.info(f"Task {self.request.id} completed successfully")
    return {'status': 'success', 'result': result}

@safe_result
def call_openai_api(model_name, system_prompt, user_request):
    logger.info("Starting OpenAI API call")
    completion = openai_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_request}
        ]
    )
    result = completion.choices[0].message.content
    logger.info("OpenAI API call completed successfully")
    return result

@safe_result
def call_claude_api(model_name, system_prompt, user_request):
    logger.info("Starting Claude API call")
    messages = [
        {"role": "user", "content": user_request}
    ]

    message = anthropic_client.messages.create(
        model=model_name,
        max_tokens=1024,
        system=system_prompt,
        messages=messages
    )

    try:
        result = json.loads(message.content[0].text)
    except json.JSONDecodeError:
        result = message.content[0].text

    logger.info("Claude API call completed successfully")
    return result

@safe_result
def call_openai_api_img(model_name, system_prompt, user_request, image_paths=None):
    logger.info("Starting OpenAI API call with image")
    messages = [{"role": "system", "content": system_prompt}]

    if image_paths:
        for image_path in image_paths:
            base64_image = image_to_base64(image_path)
            messages.append({
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]
            })

    messages.append({"role": "user", "content": user_request})

    completion = openai_client.chat.completions.create(
        model=model_name,
        messages=messages
    )
    result = completion.choices[0].message.content
    logger.info("OpenAI API call with image completed successfully")
    return result

@safe_result
def call_claude_api_img(model_name, system_prompt, user_request, image_paths=None):
    logger.info("Starting Anthropic API call with image")
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

    try:
        result = json.loads(message.content[0].text)
    except json.JSONDecodeError:
        result = message.content[0].text

    logger.info("Anthropic API call with image completed successfully")
    return result

if __name__ == '__main__':
    argv = ['worker', '--loglevel=info', '-P', 'solo']
    app.worker_main(argv)