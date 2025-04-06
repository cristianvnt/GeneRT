from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time

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

df = scrape_archs4_coexpressed_genes("BRCA1", top_n=10)
pd.set_option("display.float_format", "{:.16f}".format)
print(df if not df.empty else "No data found.")