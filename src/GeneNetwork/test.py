import re
from typing import List, Dict, Set

def update_gene_pathway_counts(
    entry_lines: List[str],
    gene_pathway_counts: Dict[str, int],
    seen_in_pathway: Set[str]
) -> None:
    for line in entry_lines:
        matches = re.findall(r'hsa:(\d+)', line)
        for gene_id in matches:
            if gene_id not in seen_in_pathway:
                gene_pathway_counts[gene_id] = gene_pathway_counts.get(gene_id, 0) + 1
                seen_in_pathway.add(gene_id)

# === Simulated pathways ===
# These represent 3 separate pathways' entry blocks
pathway1 = [
    '<entry id="1" name="hsa:5893 hsa:1234" type="gene"',
    '<entry id="2" name="hsa:1111" type="gene"',
'<entry id="5" name="hsa:5932 hsa:7979 hsa:2222" type="gene"',

]

pathway2 = [
    '<entry id="3" name="hsa:5893 hsa:7979" type="gene"',
'<entry id="5" name="hsa:5932 hsa:7979 hsa:2222" type="gene"',


]

pathway3 = [
    '<entry id="4" name="hsa:5932 hsa:7979 hsa:2222" type="gene"',
]

# === Main demo execution ===
gene_pathway_counts = {}

# Simulate processing each pathway
for pathway_entries in [pathway1, pathway2, pathway3]:
    seen_in_pathway = set()
    update_gene_pathway_counts(pathway_entries, gene_pathway_counts, seen_in_pathway)

# === Output result ===
print("Frequency of genes across pathways:")
for gene, count in gene_pathway_counts.items():
    print(f"hsa:{gene} → {count} pathway(s)")
