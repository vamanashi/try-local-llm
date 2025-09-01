#!/usr/bin/env python3
import sys
from openai import OpenAI

def chat(message):
    client = OpenAI(base_url="http://localhost:1234/v1")
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python try-llm-studio-api.py \"メッセージ\"")
        sys.exit(1)
    
    print(chat(sys.argv[1]))