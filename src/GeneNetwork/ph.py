# Python translation of the Java classes

import os
import requests
from typing import List
from dataclasses import dataclass
from dotenv import load_dotenv
import json

load_dotenv()


@dataclass
class KGMLSections:
    entry_lines: List[str]
    relation_lines: List[str]


class KGMLGeneInteractionUtils:

    @staticmethod
    def extract_entry_and_relation_blocks(xml: str) -> KGMLSections:
        entries = []
        relations = []

        lines = xml.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("<entry"):
                entries.append(line)
            elif line.startswith("<relation"):
                relation_block = [line]
                i += 1
                while i < len(lines) and "<subtype" not in lines[i]:
                    relation_block.append(lines[i].strip())
                    i += 1
                if i < len(lines):
                    relation_block.append(lines[i].strip())
                relations.append('\n'.join(relation_block))
            i += 1

        return KGMLSections(entries, relations)


class Logic:

    @staticmethod
    def fetch_pathways_for_gene(gene_id: int) -> List[str]:
        url = f"https://rest.kegg.jp/link/pathway/hsa:{gene_id}"
        response = requests.get(url)
        response.raise_for_status()
        return [line.split('\t')[1].strip() for line in response.text.splitlines() if '\t' in line]

    @staticmethod
    def fetch_first_kgmls(pathway_ids: List[str], max_items: int = 10) -> List[str]:
        kgml_list = []
        for pid in pathway_ids[:max_items]:
            cleaned_id = pid.replace("path:", "")
            url = f"https://rest.kegg.jp/get/{cleaned_id}/kgml"
            response = requests.get(url)
            response.raise_for_status()
            kgml_list.append(response.text)
        return kgml_list


    @staticmethod
    def create_qwen_entry_id_prompt_from_list(entry_lines: List[str], gene_id: str) -> str:
        entry_text = '\n'.join(entry_lines)
        return f'''
        From the list of <entry> elements below, find the one whose `name` attribute contains the gene ID "{gene_id}".

        Return ONLY the corresponding `entry id` in this JSON format:
        {{
          "entry_id": "ID"
        }}

        Entry list:
        {entry_text}
        '''


    # @staticmethod
    # def ask_gemma_for_entry_id(entry_lines: List[str], gene_id: str) -> str:
    #     prompt = Logic.create_qwen_entry_id_prompt_from_list(entry_lines, gene_id)
    #     result = Logic._call_llm(prompt)
    #     try:
    #         return result.get("entry_id", "")
    #     except:
    #         return ""
    #
    # @staticmethod
    # def _call_llm(prompt: str):
    #     HF_TOKEN = os.getenv("HF_TOKEN")
    #     HF_API_URL = "https://api-inference.huggingface.co/models/google/gemma-3-27b-it"
    #
    #     headers = {
    #         "Authorization": f"Bearer {HF_TOKEN}",
    #         "Content-Type": "application/json"
    #     }
    #
    #     data = {
    #         "inputs": prompt,
    #         "parameters": {
    #             "max_new_tokens": 200,
    #             "temperature": 0.3,
    #             "return_full_text": False
    #         }
    #     }
    #
    #     response = requests.post(HF_API_URL, headers=headers, json=data)
    #
    #     if response.status_code != 200:
    #         raise Exception(f"Error {response.status_code}: {response.text}")
    #
    #     try:
    #         raw = response.text
    #         json_start = raw.find("{")
    #         json_end = raw.rfind("}") + 1
    #         if json_start != -1 and json_end > json_start:
    #             return json.loads(raw[json_start:json_end])
    #         else:
    #             array_start = raw.find("[")
    #             array_end = raw.rfind("]") + 1
    #             return json.loads(raw[array_start:array_end])
    #     except Exception as e:
    #         print("Raw response that failed to parse:", response.text)
    #         raise e
