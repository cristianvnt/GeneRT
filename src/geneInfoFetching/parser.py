import re
from typing import List, Dict, Tuple

import pandas as pd
from accelerate.test_utils.scripts.test_sync import step_model


def parse_entries(entries: List[str], gene_id: str) -> pd.DataFrame:
    entry_data = []

    for line in entries:
        id_match = re.search(r'id="(\d+)"', line)
        name_match = re.search(r'name="([^"]+)"', line)

        if id_match and name_match:
            entry_id = id_match.group(1)
            name_field = name_match.group(1)
            contains_gene = f"hsa:{gene_id}" in name_field
            gene_matches = re.findall(r'hsa:(\d+)', name_field)

            entry_data.append({
                "entry_id": entry_id,
                "contains_candidate_gene": contains_gene,
                "gene_ids": gene_matches
            })

    df = pd.DataFrame(entry_data)
    candidate_entry_ids = df[df["contains_candidate_gene"]]["entry_id"].tolist()
    all_genes = sorted(set(gid for sublist in df["gene_ids"] for gid in sublist))

    return pd.DataFrame({
        "entry_ids": [candidate_entry_ids],
        "gene_participants": [all_genes]
    })


def parse_relations(entry_ids: List[str], relation_lines: List[str]) -> pd.DataFrame:
    data = []

    for relation in relation_lines:
        entry1 = re.search(r'entry1="(\d+)"', relation)
        entry2 = re.search(r'entry2="(\d+)"', relation)
        subtype = re.search(r'<subtype name="([^"]+)"', relation)

        if entry1 and entry2 and subtype:
            e1 = entry1.group(1)
            e2 = entry2.group(1)
            sub = subtype.group(1)

            if e1 in entry_ids:
                data.append({"target_entry_id": e2, "relation_type": sub})
            elif e2 in entry_ids:
                data.append({"target_entry_id": e1, "relation_type": sub})

    return pd.DataFrame(data)



#last step

def map_entry_ids_to_gene_ids(entry_lines: List[str], association_df: pd.DataFrame) -> pd.DataFrame:
    entry_id_to_genes = {}

    for line in entry_lines:
        entry_id_match = re.search(r'id="(\d+)"', line)
        name_match = re.search(r'name="([^"]+)"', line)

        if entry_id_match and name_match:
            entry_id = entry_id_match.group(1)
            gene_ids = re.findall(r'hsa:(\d+)', name_match.group(1))
            if gene_ids:
                entry_id_to_genes[entry_id] = gene_ids

    records = []
    for _, row in association_df.iterrows():
        entry_id = row["target_entry_id"]
        relation_type = row["relation_type"]
        gene_ids = entry_id_to_genes.get(entry_id)
        if gene_ids:
            for gid in gene_ids:
                records.append({"gene_id": gid, "relation_type": relation_type})
        else:
            print(f"❌ Entry ID {entry_id} not found in entries.")

    return pd.DataFrame(records)
