
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

        kgmls = Logic.fetch_first_kgmls(pathways, 4)
        print(f"Retrieved {len(kgmls)} KGML files")

        for kgml in kgmls:
            print("START\n")

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

            gene_match_info_df = parser.parse_entries(sections.entry_lines, gene_id)
            entry_ids = gene_match_info_df["entry_ids"].iloc[0]
            print(gene_match_info_df.to_dict(orient="records"))

            response_df = parser.parse_relations(entry_ids, sections.relation_lines)
            print("Response")
            print(response_df)

            result_df = parser.map_entry_ids_to_gene_ids(sections.entry_lines, response_df)
            print("Result")
            print(result_df)


        df = pd.DataFrame(list(gene_pathway_counts.items()), columns=["gene_id", "pathway_count"])
        print("DEBUG")
        top_20 = df.sort_values(by="pathway_count", ascending=False).head(20)

        print(top_20)

        top_20["similarity_score"] = 0.0

        for id_gene, row in top_20[1:].iterrows():
            gene = row["gene_id"]
            print(gene)

            try:
                related_gene_pathways = Logic.fetch_pathways_for_gene(int(gene))

                union_pathways = set(related_gene_pathways) | set(pathways)
                intersection = set(related_gene_pathways) & set(pathways)

                similarity_score = len(intersection) / len(union_pathways) if union_pathways else 0

                top_20.at[id_gene, "similarity_score"] = similarity_score

            except Exception as e:
                print(f"Error with gene {gene}: {e}")


        output_path = "top_20_genes_by_pathway.csv"
        top_20[1:].to_csv(output_path, index=False)
        print(f"\nExported to {output_path}")

    except Exception as e:
        import traceback
        print("An error occurred:")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()