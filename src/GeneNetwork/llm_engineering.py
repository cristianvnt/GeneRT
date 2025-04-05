from typing import List
import os
import requests
import json

from transformers import pipeline
from transformers import AutoProcessor, AutoModelForImageTextToText

messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe = pipeline("image-text-to-text", model="google/gemma-3-27b-it")
pipe(messages)


processor = AutoProcessor.from_pretrained("google/gemma-3-27b-it")
model = AutoModelForImageTextToText.from_pretrained("google/gemma-3-27b-it")


def create_qwen_all_entry_ids_prompt_from_list(entry_lines: List[str], gene_id: str) -> str:
    entry_text = '\n'.join(entry_lines)
    return f'''
    From the list of <entry> elements below, find ALL entries where the `name` attribute contains the gene ID "{gene_id}".
    
    Return ONLY the list of matching entry ids in this exact JSON format:
    {{
      "entry_ids": ["ID1", "ID2", "ID3"]
    }}
    
    If no entries match, return:
    {{
      "entry_ids": []
    }}
    
    Entry list:
    {entry_text}
    '''




def ask_gemma_for_all_entry_ids(entry_lines: List[str], gene_id: str) -> List[str]:
    prompt = create_qwen_all_entry_ids_prompt_from_list(entry_lines, gene_id)

    HF_TOKEN = os.getenv("HF_TOKEN")
    HF_API_URL = "https://api-inference.huggingface.co/models/google/gemma-3-27b-it"

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.3,
            "return_full_text": False
        }
    }

    response = requests.post(HF_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")

    raw = response.text
    try:
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        json_str = raw[json_start:json_end]
        parsed = json.loads(json_str)
        return parsed.get("entry_ids", [])
    except Exception as e:
        print("Failed to parse JSON from Gemma response:", raw)
        raise e
