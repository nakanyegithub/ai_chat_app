import requests
import json
from config import Config

def get_available_models():
    try:
        response = requests.get(Config.OLLAMA_TAGS_URL, timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            models = [model['name'] for model in models_data.get('models', [])]
            return models if models else ["llama2", "mistral", "codellama"]
        return ["llama2", "mistral", "codellama"]
    except Exception as e:
        print(f"Error getting models: {e}")
        return ["llama2", "mistral", "codellama"]

def ask_ollama_stream(prompt, model_name):
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }
        response = requests.post(Config.OLLAMA_API_URL, json=payload, stream=True, timeout=120)
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            yield data['response']
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
        elif response.status_code == 404:
            yield f"Model {model_name} not found. Please pull it first."
        else:
            yield f"API error: {response.status_code}"
    except requests.exceptions.Timeout:
        yield "Timeout waiting for response"
    except Exception as e:
        yield f"Connection error: {str(e)}"

def ask_ollama(prompt, model_name):
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000
            }
        }
        response = requests.post(Config.OLLAMA_API_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get('response', 'No response from model')
        elif response.status_code == 404:
            return f"Model {model_name} not found. Please pull it first."
        else:
            return f"API error: {response.status_code}"
    except requests.exceptions.Timeout:
        return "Timeout waiting for response"
    except Exception as e:
        return f"Connection error: {str(e)}"
