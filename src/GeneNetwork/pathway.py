import re
from typing import List, Dict, Set


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