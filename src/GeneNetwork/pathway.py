import re
from typing import List, Dict, Set

import pandas as pd
from sympy.physics.mechanics import pathway

from src.GeneNetwork import parser
from src.GeneNetwork.ph import KGMLGeneInteractionUtils, Logic


def process_pathway(kgml, gene_id, gene_pathway_counts, accumulated_results_df):
    sections = KGMLGeneInteractionUtils.extract_entry_and_relation_blocks(kgml)
    seen_in_pathway = set()
    update_gene_pathway_counts(sections.entry_lines, gene_pathway_counts, seen_in_pathway)

    gene_match_info_df = parser.parse_entries(sections.entry_lines, gene_id)
    entry_ids = gene_match_info_df["entry_ids"].iloc[0]

    response_df = parser.parse_relations(entry_ids, sections.relation_lines)
    result_df = parser.map_entry_ids_to_gene_ids(sections.entry_lines, response_df)

    if not response_df.empty:
        accumulated_results_df = pd.concat([accumulated_results_df, result_df], ignore_index=True)

    return accumulated_results_df



def update_gene_pathway_counts(
    entry_lines: List[str],
    gene_pathway_counts: Dict[str, int],
    seen_in_pathway: Set[str]
) -> None:
    """
    Updates the frequency dictionary with genes found in a new pathway.
    - entry_lines: list of <entry> strings from the KGML
    - gene_pathway_counts: dict tracking gene_id -> pathway count
    - seen_in_pathway: set to avoid double-counting within the same pathway
    """
    for line in entry_lines:
        matches = re.findall(r'hsa:(\d+)', line)
        for gene_id in matches:
            if gene_id not in seen_in_pathway:
                gene_pathway_counts[gene_id] = gene_pathway_counts.get(gene_id, 0) + 1
                seen_in_pathway.add(gene_id)


def compute_similarity_scores(top_20, pathways):
    top_20["similarity_score"] = 0.0

    for idx, row in top_20.iterrows():
        gene = row["gene_id"]
        try:
            related_gene_pathways = Logic.fetch_pathways_for_gene(int(gene))
            union_pathways = set(related_gene_pathways) | set(pathways)
            intersection = set(related_gene_pathways) & set(pathways)
            top_20.at[idx, "similarity_score"] = len(intersection) / len(union_pathways) if union_pathways else 0
        except Exception as e:
            print(f"Error with gene {gene}: {e}")
    return top_20