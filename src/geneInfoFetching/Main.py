import logging
from ph import *
import pandas as pd
import parser
import pathway
import Score
import CSV_export
from co_expressed_genes import scrape_archs4_coexpressed_genes, transform


def process_gene(gene_name):
    try:
        # Get gene ID from name (you'll need to implement this)
        gene_id = get_gene_id_from_name(gene_name)
        if not gene_id:
            raise ValueError(f"Could not find ID for gene: {gene_name}")

        gene_pathway_counts = pd.DataFrame(columns=["gene_id", "pathway"])
        accumulated_results_df = pd.DataFrame()

        gene_kegg_id = f"hsa:{gene_id}"
        print(f"Analyzing gene {gene_kegg_id}")

        pathways = Logic.fetch_pathways_for_gene(gene_id)
        print(f"Found {len(pathways)} pathways")

        kgmls = Logic.fetch_first_kgmls(pathways, 3)
        print(f"Retrieved {len(kgmls)} KGML files")

        # Process each pathway KGML
        for i, kgml in enumerate(kgmls):
            accumulated_results_df, gene_pathway_counts = pathway.process_pathway(
                kgml, gene_id, gene_pathway_counts, accumulated_results_df, pathways[i]
            )

        print("Physical similarities")
        print(accumulated_results_df)

        Score.mappingScore(accumulated_results_df)

        # Get top 20 genes by pathway frequency (excluding candidate gene)
        top_20 = (
            gene_pathway_counts.groupby("gene_id")["pathway"]
            .nunique()
            .reset_index(name="pathway_count")
            .sort_values(by="pathway_count", ascending=False)
            .head(20)
        )
        top_20 = top_20[top_20["gene_id"] != str(gene_id)]  # skip candidate gene

        # Compute similarity scores
        top_20 = pathway.compute_similarity_scores(top_20, pathways)
        if "pathway_count" in top_20.columns:
            top_20.drop(columns=["pathway_count"], inplace=True)

        logging.info("\nFetching co-expression genes from ARCHS4...")
        df_coexp = scrape_archs4_coexpressed_genes(gene_name, top_n=10)
        df_coexp["entrez_id"] = df_coexp["gene"].apply(transform)
        df_coexp.rename(columns={"entrez_id": "gene_id"}, inplace=True)
        df_coexp.drop(columns=["gene"], inplace=True)

        # Merge all once, then process
        df_final = pd.merge(top_20, accumulated_results_df, on="gene_id", how="outer")
        df_final = pd.merge(df_final, df_coexp, on="gene_id", how="outer")

        # Fill scores just once
        df_final["relation_score"] = df_final.get("relation_score", 0).fillna(0)
        df_final["similarity_score"] = df_final.get("similarity_score", 0).fillna(0)
        df_final["correlation"] = df_final.get("correlation", 0).fillna(0)

        # Compute total score once
        df_final["total_score"] = (
                df_final["relation_score"] +
                df_final["similarity_score"] +
                0.8 * df_final["correlation"]
        )

        # Final sort and export
        df_final = df_final.sort_values(by="total_score", ascending=False).reset_index(drop=True)
        df_final = df_final[["gene_id", "total_score", "relation_score", "similarity_score", "correlation"]]

        logging.info("Final result:")
        print(df_final)

        output_path_csv = "top_20_genes_by_pathway.csv"
        CSV_export.export_to_csv(df_final, output_path_csv)

        return df_final, gene_id

    except Exception as e:
        import traceback
        print("An error occurred:")
        print(traceback.format_exc())
        raise


def get_gene_id_from_name(gene_name):
    """Helper function to get gene ID from name using NCBI API"""
    try:
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term={gene_name}[gene]+AND+homo+sapiens[orgn]&retmode=json"
        response = requests.get(search_url)
        response.raise_for_status()
        search_json = response.json()

        if search_json["esearchresult"]["idlist"]:
            return search_json["esearchresult"]["idlist"][0]
        return None
    except Exception as e:
        print(f"Error getting gene ID: {str(e)}")
        return None