import re
from typing import List, Set, Tuple
import pandas as pd

import parser
from ph import KGMLGeneInteractionUtils, Logic

def process_pathway(
    kgml: str,
    gene_id: int,
    gene_pathway_counts: pd.DataFrame,
    accumulated_results_df: pd.DataFrame,
    pathway_id: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    sections = KGMLGeneInteractionUtils.extract_entry_and_relation_blocks(kgml)
    seen_in_pathway = set()

    # Update gene-pathway participation record
    gene_pathway_counts = update_gene_pathway_counts(sections.entry_lines, gene_pathway_counts, seen_in_pathway, pathway_id)

    # Get candidate-related entries and extract their relations
    gene_match_info_df = parser.parse_entries(sections.entry_lines, gene_id)
    entry_ids = gene_match_info_df["entry_ids"].iloc[0]

    response_df = parser.parse_relations(entry_ids, sections.relation_lines)
    result_df = parser.map_entry_ids_to_gene_ids(sections.entry_lines, response_df)

    if not response_df.empty:
        accumulated_results_df = pd.concat([accumulated_results_df, result_df], ignore_index=True)

    return accumulated_results_df, gene_pathway_counts


def update_gene_pathway_counts(
    entry_lines: List[str],
    gene_pathway_counts: pd.DataFrame,
    seen_in_pathway: Set[str],
    pathway_id: str
) -> pd.DataFrame:
    new_rows = []

    for line in entry_lines:
        matches = re.findall(r'hsa:(\d+)', line)
        for gene_id in matches:
            if gene_id not in seen_in_pathway:
                new_rows.append({"gene_id": gene_id, "pathway": pathway_id})
                seen_in_pathway.add(gene_id)

    if new_rows:
        gene_pathway_counts = pd.concat([gene_pathway_counts, pd.DataFrame(new_rows)], ignore_index=True)

    return gene_pathway_counts


def compute_similarity_scores(top_20: pd.DataFrame, reference_pathways: List[str]) -> pd.DataFrame:
    top_20["similarity_score"] = 0.0

    for idx, row in top_20.iterrows():
        gene = row["gene_id"]
        try:
            related_gene_pathways = Logic.fetch_pathways_for_gene(int(gene))
            union_pathways = set(related_gene_pathways) | set(reference_pathways)
            intersection = set(related_gene_pathways) & set(reference_pathways)
            similarity_score = len(intersection) / len(union_pathways) if union_pathways else 0
            top_20.at[idx, "similarity_score"] = similarity_score
        except Exception as e:
            print(f"Error with gene {gene}: {e}")

    return top_20
