import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise SystemExit(
        "OPENROUTER_API_KEY is missing. Add it to .env and try again."
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

model_name = "qwen/qwen3.5-flash-02-23"

messages = [
    {
        "role": "system",
        "content": "You are a helpful programming teacher.",
    },
    {
        "role": "user",
        "content": "What is Python in 2 sentences?",
    },
]

temperature = 0.0

request_preview = {
    "model": model_name,
    "messages": messages,
    "temperature": temperature,
}

print("--- Request Preview ---")
print(json.dumps(request_preview, indent=2, ensure_ascii=False))

response = client.chat.completions.create(
    model=model_name,
    messages=messages,
    temperature=temperature,
)

answer = response.choices[0].message.content

print("\n--- Answer ---")
print(answer)

print("\n--- Response Details ---")
print(f"Request ID:        {response.id}")
print(f"Model:             {response.model}")
print(f"Finish reason:     {response.choices[0].finish_reason}")

if response.usage:
    print(f"Prompt tokens:     {response.usage.prompt_tokens}")
    print(f"Completion tokens: {response.usage.completion_tokens}")
    print(f"Total tokens:      {response.usage.total_tokens}")
else:
    print("Token usage:       unavailable")
