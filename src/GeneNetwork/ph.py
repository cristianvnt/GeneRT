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


# class KGMLGeneInteractionUtils:
#
#     def extract_entry_and_relation_blocks(xml: str) -> KGMLSections:
#         entries = []
#         relations = []
#
#         lines = xml.split('\n')
#         i = 0
#         while i < len(lines):
#             line = lines[i].strip()
#             if line.startswith("<entry") and 'type="gene"' in line:
#                 entries.append(line)
#             elif line.startswith("<relation"):
#                 relation_block = [line]
#                 i += 1
#                 while i < len(lines) and "<subtype" not in lines[i]:
#                     relation_block.append(lines[i].strip())
#                     i += 1
#                 if i < len(lines):
#                     relation_block.append(lines[i].strip())
#                 relations.append('\n'.join(relation_block))
#             i += 1
#
#         return KGMLSections(entries, relations)

class KGMLGeneInteractionUtils:

    @staticmethod
    def extract_entry_and_relation_blocks(xml: str) -> KGMLSections:
        entries = []
        relations = []

        lines = xml.split('\n')
        i = 0
        last_subtype_line = None

        while i < len(lines):
            line = lines[i].strip()

            # Collect gene entries
            if line.startswith("<entry") and 'type="gene"' in line:
                entries.append(line)

            # Collect relations
            elif line.startswith("<relation"):
                relation_block = [line]
                i += 1
                found_subtype = False

                while i < len(lines) and not lines[i].strip().startswith("</relation>"):
                    content = lines[i].strip()
                    if "<subtype" in content:
                        last_subtype_line = content  # remember this as last known subtype
                        found_subtype = True
                    relation_block.append(content)
                    i += 1

                # End tag
                if i < len(lines):
                    relation_block.append(lines[i].strip())

                # If no subtype found in this block, reuse last known one
                if not found_subtype and last_subtype_line:
                    relation_block.insert(1, last_subtype_line)  # insert after <relation ...>

                relations.append('\n'.join(relation_block))

            i += 1

        return KGMLSections(entries, relations)


class Logic:

    @staticmethod
    def fetch_pathways_for_gene(gene_id: int) -> List[str]:
        url = f"https://rest.kegg.jp/link/pathway/hsa:{gene_id}"
        headers = {"User-Agent": "Mozilla/5.0"}  # added header
        response = requests.get(url,headers=headers)
        response.raise_for_status()
        return [line.split('\t')[1].strip() for line in response.text.splitlines() if '\t' in line]

    @staticmethod
    def fetch_first_kgmls(pathway_ids: List[str], max_items: int = 10) -> List[str]:
        kgml_list = []
        for pid in pathway_ids[:max_items]:
            cleaned_id = pid.replace("path:", "")
            headers = {"User-Agent": "Mozilla/5.0"}  # added header
            url = f"https://rest.kegg.jp/get/{cleaned_id}/kgml"
            response = requests.get(url,headers=headers)
            response.raise_for_status()
            kgml_list.append(response.text)
        return kgml_list

