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

## Tech Stack

- **Language:** Python
- **UI:** Tkinter
- **Data Integration:** 
  - REST APIs (NCBI Entrez, KEGG, PDB)
  - Web scraping (Selenium) for fallback data
- **Graphing:** NetworkX
- **API Testing:** Postman
- **Parsing & Handling:** JSON, XML, CSV

---

## Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Setup Instructions

1. **Clone the repository**
   ```
   git clone https://github.com/Mematoru23/PHv17.git
   cd genert
   ```

2. **Create and activate a virtual environment**
   
   Windows:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
   
   macOS/Linux:
   ```
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

4. **Install additional packages separately**
   
   Some packages might not install correctly from requirements.txt:
   ```
   pip install PyQtWebEngine==5.15.7
   pip install pyvis==0.3.2
   ```

5. **Run the application**
   ```
   python -m src.main
   ```

### Troubleshooting

- If you encounter a `ModuleNotFoundError: No module named 'PyQt5.QtWebEngineWidgets'` error, make sure you've installed PyQtWebEngine as described in step 4.
- For visualization issues, verify that pyvis is properly installed.
- If using an IDE (like PyCharm or VS Code), ensure that it's using the correct virtual environment interpreter.

---
