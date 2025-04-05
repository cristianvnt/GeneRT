from ph import *
import pandas as pd
import llm_engineering
import parser
import pathway

def main():
    try:
        gene_id = 672
        gene_pathway_counts = {}

        gene_kegg_id = f"hsa:{gene_id}"
        print(f"Analyzing gene {gene_kegg_id}")

        pathways = Logic.fetch_pathways_for_gene(gene_id)
        print(f"Found {len(pathways)} pathways")

        kgmls = Logic.fetch_first_kgmls(pathways, 10)
        print(f"Retrieved {len(kgmls)} KGML files")

        for x in kgmls:
            #print(f"\nAnalyzing pathway {x}")
            print("START\n")
            kgml = x


            sections = KGMLGeneInteractionUtils.extract_entry_and_relation_blocks(kgml)
            print(f"Found {len(sections.entry_lines)} entries and {len(sections.relation_lines)} relations")

            print("[ENTRY LINES SAMPLE (first 3)]")
            for entry in sections.entry_lines[:10]:  # Show only first 3 to avoid cluttering output
                print(entry)

            print("\n[RELATION LINES SAMPLE (first 3)]")
            for rel in sections.relation_lines[:3]:  # Show only first 3 to avoid cluttering output
                print(rel)

            print(f"\nSearching for entries with gene ID {gene_id}...")
            print(sections.entry_lines)

            seen_in_pathway = set()
            pathway.update_gene_pathway_counts(sections.entry_lines, gene_pathway_counts, seen_in_pathway)
            # entry_ids = llm_engineering.find_gene_entries(sections.entry_lines,  gene_id)
            # print(entry_ids)
            # print(sections.entry_lines)
            dict=parser.parse_entries(sections.entry_lines,gene_id)
            print(dict)
            response=parser.parse_relations(dict["entry_ids"],sections.relation_lines)
            print("Response")
            print(response)

            result=parser.map_entry_ids_to_gene_ids(sections.entry_lines,response)
            print("Result")
            print(result)

            #final_result_parsed=llm_engineering.resolve_entry_ids_to_genes(result)

        df = pd.DataFrame(list(gene_pathway_counts.items()), columns=["gene_id", "pathway_count"])
        top_20 = df.sort_values(by="pathway_count", ascending=False).head(20)

        print(top_20[1:])

    except Exception as e:
        import traceback
        print("An error occurred:")
        print(traceback.format_exc())  # This will print the full stack trace


if __name__ == "__main__":
    main()