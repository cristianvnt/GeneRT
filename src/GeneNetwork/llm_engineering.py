import json
import re
from typing import List
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Global model pipeline to avoid reinitializing
global_pipe = None


def initialize_qwen():
    """Initialize Qwen model without quantization"""
    global global_pipe

    if global_pipe is None:
        print("Initializing Qwen model...")
        # Use a smaller model that can fit in CPU memory
        model_id = "Qwen/Qwen2.5-Omni-7B"

        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )

        global_pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

    return global_pipe


def create_entry_prompt(entry_lines: List[str], gene_id: str) -> str:
    """Create prompt for finding gene entries"""
    entry_text = '\n'.join(entry_lines)
    return f'''
    Analyze this entries data and find all entries containing gene hsa:{gene_id}.
    Return ONLY a JSON object with this exact format:
    {{
      "entry_ids": ["123", "456"],
    }}

    Rules:
    1. Include entries where hsa:{gene_id} appears in the name attribute
    2. Return empty lists if no matches found
    3. Only return the JSON object, no additional text

    entries:
    {entry_text}
    '''


def find_gene_entries(entries: List[str], gene_id: str) -> List[str]:
    """Find all entries for a specific gene using regex pattern matching"""

    print(f"Searching for gene hsa:{gene_id} in {len(entries)} entries...")
    result_ids = []
    search_pattern = rf'name="[^"]*hsa:{gene_id}[^"]*"'

    for entry in entries:
        if re.search(search_pattern, entry):
            # Extract ID from entry line
            match = re.search(r'id="([^"]+)"', entry)
            if match:
                entry_id = match.group(1)
                result_ids.append(entry_id)

    return result_ids