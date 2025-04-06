import requests


class GeneDrugTargetFinder:
    def __init__(self, gene_symbol="EGFR"):
        self.gene_symbol = gene_symbol

    def find_info(self):
        print(f"Finding disease associations and drug targets for gene: {self.gene_symbol}")

        try:
            # 1. Obține datele KEGG
            kegg_gene_id = f"hsa:{self.gene_symbol}"
            print(f"Fetching KEGG data for {kegg_gene_id}...")
            kegg_gene_data = self.get_kegg_gene_info(kegg_gene_id)

            # 2. Afișează bolile asociate
            diseases = self.extract_diseases(kegg_gene_data)
            if diseases:
                print(f"\nDiseases associated with {self.gene_symbol}:")
                for disease_id, disease_name in diseases:
                    print(f"- {disease_id}: {disease_name}")
            else:
                print(f"\nNo diseases found for {self.gene_symbol}.")

            # 3. Afișează medicamentele asociate (targets)
            drug_targets = self.extract_drug_targets(kegg_gene_data)
            if drug_targets:
                print(f"\nDrug targets associated with {self.gene_symbol}:")
                for drug_name, drug_ids in drug_targets:
                    print(f"- {drug_name}: {' '.join(drug_ids)}")
            else:
                print(f"\nNo drug targets found for {self.gene_symbol}.")

        except Exception as e:
            print(f"Error: {str(e)}")

    def get_kegg_gene_info(self, kegg_id):
        """Cere informațiile brute din KEGG"""
        kegg_url = f"http://rest.kegg.jp/get/{kegg_id}"
        response = requests.get(kegg_url)
        response.raise_for_status()
        return self.parse_kegg_response(response.text)

    def parse_kegg_response(self, text):
        """Parsează fișierul plat KEGG într-un dicționar"""
        result = {}
        current_key = None
        current_value = ""

        for line in text.splitlines():
            if line[:12].strip().isupper():
                if current_key:
                    result[current_key] = current_value.strip()
                current_key = line[:12].strip()
                current_value = line[12:].strip()
            else:
                current_value += "\n" + line.strip()

        if current_key:
            result[current_key] = current_value.strip()

        return result

    def extract_diseases(self, kegg_data):
        """Extrage bolile asociate din secțiunea DISEASE"""
        diseases = []

        if 'DISEASE' in kegg_data:
            for line in kegg_data['DISEASE'].split('\n'):
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    disease_id = parts[0]
                    disease_name = parts[1]
                    diseases.append((disease_id, disease_name))

        return diseases

    def extract_drug_targets(self, kegg_data):
        """Extrage medicamentele din secțiunea DRUG_TARGET"""
        drug_targets = []

        if 'DRUG_TARGET' in kegg_data:
            for line in kegg_data['DRUG_TARGET'].split('\n'):
                if ':' not in line:
                    continue
                left, right = line.split(':', 1)
                drug_name = left.strip()
                drug_ids = right.strip().split()
                drug_targets.append((drug_name, drug_ids))

        return drug_targets


if __name__ == "__main__":
    finder = GeneDrugTargetFinder("EGFR")  # Poți schimba cu orice genă
    finder.find_info()
