from difflib import unified_diff

from ph import *
import pandas as pd
import llm_engineering
import parser
import pathway
import Score
from src.GeneNetwork import CSV_export


def main():
    try:
        gene_id = 672
        gene_pathway_counts = {}
        accumulated_results_df = pd.DataFrame()


        gene_kegg_id = f"hsa:{gene_id}"
        print(f"Analyzing gene {gene_kegg_id}")

        pathways = Logic.fetch_pathways_for_gene(gene_id)

        print(f"Found {len(pathways)} pathways")

        kgmls = Logic.fetch_first_kgmls(pathways, 4)
        print(f"Retrieved {len(kgmls)} KGML files")

        for kgml in kgmls:
            accumulated_results_df = pathway.process_pathway(kgml, gene_id, gene_pathway_counts, accumulated_results_df)


        print("Phisical similarities")
        print(accumulated_results_df)
        Score.mappingScore(accumulated_results_df)
        print(accumulated_results_df)

        print("DEBUG")


        df = pd.DataFrame(list(gene_pathway_counts.items()), columns=["gene_id", "pathway_count"])
        top_20 = df.sort_values(by="pathway_count", ascending=False).head(20)
        top_20=top_20[1:]
        top_20.drop(columns=["pathway_count"])

        #print(top_20)

        pathway.compute_similarity_scores(top_20,pathways)
        print(top_20)

        #unifies

        df_merged = pd.merge(top_20, accumulated_results_df, on="gene_id", how="outer")

        # Fill NaNs with 0 for missing scores
        df_merged["relation_score"] = df_merged["relation_score"].fillna(0)
        df_merged["similarity_score"] = df_merged["similarity_score"].fillna(0)

        # Create total score
        df_merged["total_score"] = df_merged["relation_score"] + df_merged["similarity_score"]

        # Sort by total_score descending
        df_merged = df_merged.sort_values(by="total_score", ascending=False)

        # Reset index
        df_merged.reset_index(drop=True, inplace=True)

        print("Final show")
        # Show result
        print(df_merged)

        output_path = "top_20_genes_by_pathway.csv"
        CSV_export.export_to_csv(top_20, output_path)

    except Exception as e:
        import traceback
        print("An error occurred:")
        print(traceback.format_exc())


if __name__ == "__main__":
    main()