import json

import requests
import pandas as pd
import time
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By

def scrape_archs4_coexpressed_genes(gene: str, top_n: int = 10) -> pd.DataFrame:
    url = f"https://maayanlab.cloud/archs4/gene/{gene.upper()}"

    # Setup headless Chrome
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(3)  # Wait for JavaScript to load the table

        # Find rows in the co-expression table
        rows = driver.find_elements(By.CSS_SELECTOR, "#tablecor tbody tr")[:top_n]
        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            gene_name = cols[1].text.strip()
            corr = float(cols[2].text.strip())
            data.append({"gene": gene_name, "correlation": corr})

        return pd.DataFrame(data)

    finally:
        driver.quit()

def send_get_request(url_string):
    response = requests.get(url_string)
    response.raise_for_status()
    return response.text

def transform(gene_name: str):
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term={gene_name}[gene]+AND+homo+sapiens[orgn]&retmode=json"
    try:
        search_response = send_get_request(search_url)
        search_json = json.loads(search_response)
        id_list = search_json["esearchresult"]["idlist"]
        return id_list[0] if id_list else "Not found"
    except Exception as e:
        print(f"Error fetching Entrez ID for {gene_name}: {e}")
        return "Error"
