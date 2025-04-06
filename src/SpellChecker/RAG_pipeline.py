import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_gene_list():
    """Load gene list from KEGG database"""
    try:
        response = requests.get("https://rest.kegg.jp/list/hsa")
        gene_list = [line.split("\t")[1].split(";")[0].strip() for line in response.text.strip().split("\n")]
        print(f"Loaded {len(gene_list)} genes from KEGG")
        return gene_list
    except Exception as e:
        print(f"Error loading gene list: {e}")
        return []


def build_index(gene_list):
    """Build embeddings and FAISS index for gene names"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(gene_list)

    # Build FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))

    return model, index


def retrieve_candidates(user_input, model, index, gene_list, top_k=3):
    """Retrieve similar gene candidates using embedding search"""
    user_vec = model.encode([user_input])
    distances, indices = index.search(np.array(user_vec), top_k)
    candidates = [gene_list[i] for i in indices[0]]
    return candidates, distances[0]


def ask_llm_for_correction(user_input, suggestions, distances):
    """Ask LLM to determine the most likely intended gene name"""
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

    # Format suggestions with their distances to help the LLM decide
    suggestions_with_scores = [f"{gene} (distance: {distance:.4f})"
                               for gene, distance in zip(suggestions, distances)]

    prompt = f"""
    The user typed a potentially incorrect gene name: "{user_input}".

    Based on the following possible gene matches (lower distance means more similar):
    {', '.join(suggestions_with_scores)}

    Which one is the most likely intended gene name? Return only the corrected name.
    If none seem likely, respond with "No close match found".
    """

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Fallback to the closest match by distance
        return suggestions[0] if suggestions else "No close match found"


def main():
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Please set it using: export OPENAI_API_KEY='your-key-here' (Linux/Mac)")
        print("or: set OPENAI_API_KEY=your-key-here (Windows)")
        return

    # Load gene list and build index
    print("Loading gene data...")
    gene_list = load_gene_list()
    if not gene_list:
        return

    print("Building search index...")
    model, index = build_index(gene_list)

    # Interactive loop
    print("\nGene Name Spell Checker")
    print("Enter a gene name to check (or 'exit' to quit)")

    while True:
        user_input = input("\nEnter gene name: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break

        if not user_input:
            continue

        print(f"Checking: '{user_input}'")
        candidates, distances = retrieve_candidates(user_input, model, index, gene_list)

        if candidates:
            print(f"Finding best match among: {', '.join(candidates)}")
            suggested_name = ask_llm_for_correction(user_input, candidates, distances)
            print(f"Suggested gene name: {suggested_name}")
        else:
            print("No gene candidates found")


if __name__ == "__main__":
    main()