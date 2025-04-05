import json
from typing import List
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from transformers import BitsAndBytesConfig

# Quantization configuration for memory efficiency
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4"
)


def initialize_qwen():
    """Initialize Qwen model with quantization"""
    model_id = "Qwen/Qwen2.5-Omni-7B"

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        quantization_config=quant_config,
        torch_dtype=torch.bfloat16
    )

    return pipeline("text-generation", model=model, tokenizer=tokenizer)


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


def find_gene_entries(entries: List[str], gene_id: str) -> dict:
    """Find all entries for a specific gene"""
    # Initialize Qwen pipeline


    qwen_pipe = initialize_qwen()

    # Create chunks if KGML is too large
    # entry_lines = [line for line in kgml_text.split('\n') if '<entry' in line]
    # chunk_size = 20  # Process 20 entries at a time
    # results = []

    prompt = create_entry_prompt(entries, gene_id)

        # Generate response
    response = qwen_pipe(
        prompt,
        max_new_tokens=200,
        temperature=0.1,  # Lower for more deterministic results
        do_sample=False
        )

    try:
        # Extract JSON from response
        json_str = response[0]['generated_text'].split('{', 1)[-1]
        json_str = '{' + json_str.rsplit('}', 1)[0] + '}'
    except Exception as e:
        print(f"Error parsing response: {e}")

    # Combine results from all chunks


    return json.loads(json_str)