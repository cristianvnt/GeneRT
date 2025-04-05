from ph import *
import llm_engineering


def main():
    try:
        gene_id = 7157
        gene_kegg_id = f"hsa:{gene_id}"
        print(f"Analyzing gene {gene_kegg_id}")

        pathways = Logic.fetch_pathways_for_gene(gene_id)
        print(f"Found {len(pathways)} pathways")

        kgmls = Logic.fetch_first_kgmls(pathways, 3)
        print(f"Retrieved {len(kgmls)} KGML files")

        i = 0
        print(f"\nAnalyzing pathway {pathways[i]}")
        kgml = kgmls[i]

        sections = KGMLGeneInteractionUtils.extract_entry_and_relation_blocks(kgml)
        print(f"Found {len(sections.entry_lines)} entries and {len(sections.relation_lines)} relations")

        print("[ENTRY LINES SAMPLE (first 3)]")
        for entry in sections.entry_lines[:3]:  # Show only first 3 to avoid cluttering output
            print(entry)

        print("\n[RELATION LINES SAMPLE (first 3)]")
        for rel in sections.relation_lines[:3]:  # Show only first 3 to avoid cluttering output
            print(rel)

        print("\nSearching for entries with gene ID 7157...")
        entry_ids = llm_engineering.find_gene_entries(sections.entry_lines, "7157")
        print("Matching entry IDs:", entry_ids)

    except Exception as e:
        import traceback
        print("An error occurred:")
        print(traceback.format_exc())  # This will print the full stack trace


if __name__ == "__main__":
    main()