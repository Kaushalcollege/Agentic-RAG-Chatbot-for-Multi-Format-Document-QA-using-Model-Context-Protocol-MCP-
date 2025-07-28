# backend/utils/llm.py

import requests
from transformers import pipeline
from config import GROQ_API_KEY, GROQ_MODEL, FALLBACK_MODEL, USE_FALLBACK

# Local fallback pipeline
# fallback_pipe = pipeline("text-generation", model=FALLBACK_MODEL, max_new_tokens=256)

def query_groq(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Groq failed: {response.status_code} - {response.text}")

def query_fallback(prompt: str) -> str:
    result = fallback_pipe(prompt, do_sample=True)[0]['generated_text']
    return result

def generate_response(prompt: str) -> str:
    try:
        return query_groq(prompt)
    except Exception as e:
        print(f"[❌ Groq API failed] {e}")
        return "Groq failed and fallback is disabled."
