import re
from typing import List, Dict, Tuple

from accelerate.test_utils.scripts.test_sync import step_model




def parse_entries(entries: List[str], gene_id: str) -> Dict[str, List[str]]:
    entry_ids = []
    gene_participants = []

    for line in entries:
        # Match the id="123" part
        id_match = re.search(r'id="(.*?)"', line)
        name_match = re.search(r'name="(.*?)"', line)

        if id_match and name_match:
            entry_id = id_match.group(1)
            name_field = name_match.group(1)

            # Check if it contains the gene of interest
            if f"hsa:{gene_id}" in name_field:
                entry_ids.append(entry_id)

            # Extract all hsa: numbers from the name field
            genes = re.findall(r'hsa:(\d+)', name_field)
            gene_participants.extend(genes)

    return {
        "entry_ids": sorted(set(entry_ids)),
        "gene_participants": sorted(set(gene_participants))
    }



def parse_relations(entry_ids: List[str], relation_lines: List[str]) -> List[Tuple[str, str]]:
    related_pairs = []

    for relation in relation_lines:
        # Match entry1, entry2, and subtype name
        entry1 = re.search(r'entry1="(\d+)"', relation)
        entry2 = re.search(r'entry2="(\d+)"', relation)
        subtype = re.search(r'<subtype name="([^"]+)"', relation)

        if entry1 and entry2 and subtype:
            e1 = entry1.group(1)
            e2 = entry2.group(1)
            sub = subtype.group(1)

            # If either entry1 or entry2 matches a known entry_id
            if e1 in entry_ids:
                related_pairs.append((e2, sub))
            elif e2 in entry_ids:
                related_pairs.append((e1, sub))

    return related_pairs


#last step

def map_entry_ids_to_gene_ids(entry_lines: List[str], association_list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    entry_id_to_genes = {}

    # Build mapping from entry id -> gene ids
    for line in entry_lines:
        entry_id_match = re.search(r'id="(\d+)"', line)
        name_match = re.search(r'name="([^"]+)"', line)

        if entry_id_match and name_match:
            entry_id = entry_id_match.group(1)
            gene_ids = re.findall(r'hsa:(\d+)', name_match.group(1))
            if gene_ids:
                entry_id_to_genes[entry_id] = gene_ids

    # Map association entry ids to gene ids
    result = []
    for entry_id, relation_type in association_list:
        gene_ids = entry_id_to_genes.get(entry_id)
        if gene_ids:
            for gid in gene_ids:
                result.append((gid, relation_type))
        else:
            print(f"❌ Entry ID {entry_id} not found in entries.")

    return result
