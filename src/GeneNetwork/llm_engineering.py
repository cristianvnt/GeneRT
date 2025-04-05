import os
import json
import re
from typing import List, Dict, Tuple
from dotenv import load_dotenv
import openai
from openai import OpenAI

# Load API key from environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# def create_entry_prompt(entry_lines: List[str], gene_id: str) -> str:
#     entry_text = '\n'.join(entry_lines)
#     return f'''
#     From the list of XML-like gene <entry> lines below:
#
#     1. Extract only the entry ID (from the `id` field of the entry) where the `name` field contains "hsa:{gene_id}". Include this in the "entry_ids" list.
#     2. For every <entry>, extract all gene identifiers in the `name` field that begin with "hsa:". Remove the "hsa:" prefix and collect those numbers in the "gene_participants" list.
#
#     Return ONLY a valid JSON object in the exact format below:
#     {{
#       "entry_ids": ["123"],
#       "gene_participants": ["456", "7890"]
#     }}
#
#     Do not return any explanation or commentary, just the JSON.
#
#     Example input:
#     <entry id="12" name="hsa:7157 hsa:1234" />
#     <entry id="13" name="hsa:5678" />
#
#     Example output if gene_id is 7157:
#     {{
#       "entry_ids": ["12"],
#       "gene_participants": ["7157", "1234", "5678"]
#     }}
#
#     Now process this real input:
#     {entry_text}
#     '''



# def create_entry_prompt(entry_lines: List[str], gene_id: str) -> str:
#     entry_text = '\n'.join(entry_lines)
#     return f'''
#     From the list of XML-like gene <entry> lines below:
#
#     1. Extract only the entry ID (from the `id` field of the entry) where the `name` field contains "hsa:{gene_id}". Include this in the "entry_ids" list.
#
#     Return ONLY a valid JSON object in the exact format below:
#     {{
#       "entry_ids": ["123"],
#     }}
#
#     Do not return any explanation or commentary, just the JSON.
#
#     Example input:
#     <entry id="12" name="hsa:7157 hsa:1234" />
#     <entry id="13" name="hsa:5678" />
#
#     Example output if gene_id is 7157:
#     {{
#       "entry_ids": ["12"],
#     }}
#
#     Now process this real input:
#     {entry_text}
#     '''

def create_prompt(entry_lines: List[str]):
    entry_text = "\n".join(entry_lines)
    return f'''
    You are given two pieces of data:

1. A list of relation pairs, where each tuple contains an entry ID and a relation type:
[
  ("332", "phosphorylation"),
  ("325", "binding/association")
]

2. A list of <entry> elements in XML-like format:
<entry id="65" name="hsa:7156 hsa:8940" type="gene"
<entry id="66" name="hsa:641" type="gene"
<entry id="67" name="hsa:7979" type="gene"
<entry id="68" name="hsa:5893" type="gene"
<entry id="69" name="hsa:4361" type="gene"
<entry id="70" name="hsa:10111" type="gene"
<entry id="325" name="hsa:5932" type="gene"
<entry id="332" name="hsa:472" type="gene"

Your task:

Match each entry ID from the relation pairs with its corresponding hsa gene ID from the entry list.

Then return a new list of (gene_id, relation_type) pairs, where gene_id is extracted from the `name` field (removing the "hsa:" prefix).

Format your response as valid JSON:
[
  ["472", "phosphorylation"],
  ["5932", "binding/association"]
]
Only return the JSON. No extra explanation.
Here is the list of entries:
{entry_text}
    '''


def find_gene_entries(entries: List[str], gene_id: str) -> Dict:
    print(f"Searching for gene hsa:{gene_id} in {len(entries)} entries using OpenAI ChatGPT API...")


    all_entry_ids = []
    all_gene_participants = []
    client = OpenAI(
        # This is the default and can be omitted
        api_key=openai.api_key,
    )
    input_text="\n".join(entries)
    prompt = create_prompt(input_text, gene_id)

    try:
        response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":"You are a bioinformatician which analyze a set of large data and make correlation between a given id and the real id of a gene"},
                    {"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.1
            )
        result_text = response.choices[0].message.content

        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            json_str = json_match.group(0)
            result_data = json.loads(json_str)
            all_entry_ids.extend(result_data.get("entry_ids", []))
            all_gene_participants.extend(result_data.get("gene_participants", []))
        else:
            print("No JSON found in response for current chunk")
    except Exception as e:
        print(f"Error processing chunk: {e}")

    all_entry_ids = sorted(set(id.strip() for id in all_entry_ids if id.strip()))
    all_gene_participants = sorted(set(id.strip() for id in all_gene_participants if id.strip()))

    return {
        "entry_ids": all_entry_ids,
        "gene_participants": all_gene_participants
    }

def resolve_entry_ids_to_genes(entries: List[str]) -> List[Tuple[str, str]]:
    client = OpenAI(api_key=openai.api_key)
    prompt = create_prompt(entries)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a bioinformatician analyzing biological pathway relations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=512,
            temperature=0.1
        )
        result_text = response.choices[0].message.content
        json_match = re.search(r'\[[\s\S]*\]', result_text)

        if json_match:
            return json.loads(json_match.group(0))
        else:
            print("No JSON array found.")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []
