import os
import json
import re
import requests
from typing import List, Dict
from dotenv import load_dotenv

API_URL = "https://router.huggingface.co/together/v1/chat/completions"

def create_entry_prompt(entry_lines: List[str], gene_id: str) -> str:
    entry_text = '\n'.join(entry_lines)
    return f'''
    A From the list of XML-like gene <entry> lines below:

    1. Extract only the entry ID (from the `id` field) where the `name` field contains the gene ID "hsa:{gene_id}". Include this in the "entry_ids" list.
    2. For every <entry>, extract all gene identifiers in the `name` field that begin with "hsa:". Remove the "hsa:" prefix and collect those numbers in the "gene_participants" list.

    Return ONLY a valid JSON object in the exact format below:
    {{
      "entry_ids": ["..."],
      "gene_participants": ["...", "..."]
    }}

    Do not return any explanation or commentary, just the JSON.

    Example input:
    <entry id="12" name="hsa:7157 hsa:1234" />
    <entry id="13" name="hsa:5678" />

    Example output if gene_id is 7157:
    {{
      "entry_ids": ["12"],
      "gene_participants": ["7157", "1234", "5678"]
    }}

    Now process this real input:
    {entry_text}
    '''


def find_gene_entries(entries: List[str], gene_id: str) -> Dict:
    print(f"Searching for gene hsa:{gene_id} in {len(entries)} entries using Together Inference API...")

    chunk_size = 50
    chunked_entries = [entries[i:i + chunk_size] for i in range(0, len(entries), chunk_size)]

    all_entry_ids = []
    all_gene_participants = []

    load_dotenv()
    token = os.getenv("HF_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}

    for i, chunk in enumerate(chunked_entries):
        print(f"→ Processing chunk {i + 1}/{len(chunked_entries)}")
        prompt = create_entry_prompt(chunk, gene_id)

        try:
            payload = {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "model": "Qwen/Qwen2.5-7B-Instruct-Turbo"
            }
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result_text = response.json()["choices"][0]["message"]["content"]

            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                all_entry_ids.extend(result.get("entry_ids", []))
                all_gene_participants.extend(result.get("gene_participants", []))
            else:
                print("No JSON found in response for current chunk")
        except Exception as e:
            print(f"Error parsing or retrieving from Together Inference API: {e}")
            print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")

    all_entry_ids = sorted(set(id.strip() for id in all_entry_ids if id.strip()))
    all_gene_participants = sorted(set(id.strip() for id in all_gene_participants if id.strip()))

    return {
        "entry_ids": all_entry_ids,
        "gene_participants": all_gene_participants
    }
