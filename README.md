# Gene RT – Gene Exploration & Drug Repurposing App

**Gene RT** is a Python-based desktop application built to support both **bioinformaticians** and **individuals affected by rare genetic diseases**. It enables deep exploration of gene data, visualizes gene-gene interaction networks, and intelligently suggests repurposable drugs — all in a clean, intuitive interface.

---

## Features

-  **Gene Lookup**  
  Enter a gene name to retrieve:
    - Full gene name and biological function
    - Pathways and diseases associated
    - Protein encoded by the gene

-  **Interactive Gene Network**  
  Visual graph showing related genes based on shared pathways. Clickable nodes to update context.

-  **Drug Repurposing Engine**  
  Suggests known drugs used to target similar genes using a **Repurposing Score** heuristic.

-  **Protein Structure Viewer**  
  Visualizes 3D protein structures encoded by genes.

-  **Public Mode (Non-Expert Users)**  
  Search by disease name and get a simplified overview, involved genes, and potential treatment options — free of overwhelming medical jargon.

---

##  Tech Stack

- **Language:** Python
- **UI:** Tkinter
- **Data Integration:** 
  - REST APIs (NCBI Entrez, KEGG, PDB)
  - Web scraping (Selenium) for fallback data
- **Graphing:** NetworkX
- **API Testing:** Postman
- **Parsing & Handling:** JSON, XML, CSV

---


