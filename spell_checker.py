import os
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from openai import OpenAI

load_dotenv()

def load_gene_list():
    try:
        with open("list.txt", "r") as file:
            return [line.strip() for line in file.readlines()]
    except Exception:
        return []

def build_index(gene_list):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(gene_list)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return model, index

def retrieve_candidates(user_input, model, index, gene_list, top_k=3):
    user_vec = model.encode([user_input])
    distances, indices = index.search(np.array(user_vec), top_k)
    candidates = [gene_list[i] for i in indices[0]]
    return candidates, distances[0], user_vec

def fuzzy_match(user_input, gene_list, threshold=85):
    if len(user_input) <= 4:
        threshold = 70
    match, score, _ = process.extractOne(user_input, gene_list)
    return match if score >= threshold else None

def find_closest_levenshtein(user_input, gene_list):
    return min(gene_list, key=lambda g: Levenshtein.distance(user_input, g))

def ask_llm_for_correction(user_input, suggestions, distances):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return suggestions[0] if suggestions else "No close match found"

    prompt = f"""
The user typed a potentially incorrect gene name: "{user_input}".
Here are some similar options:
{', '.join(f"{g} (distance: {d:.4f})" for g, d in zip(suggestions, distances))}

Only choose from the list. Return the most likely intended gene name.
If none are correct, respond with "No close match found".
"""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return suggestions[0] if suggestions else "No close match found"

def suggest_gene_name(user_input):
    gene_list = [g.strip().upper() for g in load_gene_list()]
    if not gene_list:
        return "No gene list found"

    user_input = user_input.strip().upper()

    # Exact match
    if user_input in gene_list:
        return user_input

    # Fuzzy match with dynamic threshold for short names
    fuzzy = fuzzy_match(user_input, gene_list, threshold=80 if len(user_input) <= 5 else 85)
    if fuzzy:
        return fuzzy

    # Levenshtein fallback
    lev_match = find_closest_levenshtein(user_input, gene_list)
    max_allowed_dist = max(1, len(user_input) // 3)  # e.g., 4-letter input allows dist 1
    if Levenshtein.distance(user_input, lev_match) <= max_allowed_dist:
        return lev_match

    #fallback
    if len(user_input) > 5:
        model, index = build_index(gene_list)
        candidates, distances, _ = retrieve_candidates(user_input, model, index, gene_list)
        if distances[0] < 0.4:
            return candidates[0]

    # 5. Nothing worked
    return "No close match found"

if __name__ == "__main__":
    examples = ["bc1", "akt", "tp5", "sos1", "abcd"]
    for gene in examples:
        corrected = suggest_gene_name(gene)
        print(f"Input: {gene} → Suggested: {corrected}")