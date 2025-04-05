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
        print("[ENTRY LINES]")
        for entry in sections.entry_lines:
            print(entry)

        print("\n[RELATION LINES]")
        for rel in sections.relation_lines:
            print(rel)

        print("finish")

        entry_ids = llm_engineering.ask_gemma_for_all_entry_ids(sections.entry_lines, "7157")
        print("Matching entry IDs:", entry_ids)

    except Exception as e:
        print("An error occurred:", str(e))


if __name__ == "__main__":
    main()
