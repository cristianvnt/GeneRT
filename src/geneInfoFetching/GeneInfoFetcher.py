import requests
import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
import webview


class GeneInfoApp:
    def __init__(self, root):
        self.root = root
        root.title("Gene Information Finder")
        root.geometry("900x700")

        self.title_font = Font(family='Helvetica', size=12, weight='bold')
        self.header_font = Font(family='Helvetica', size=11, weight='bold')
        self.normal_font = Font(family='Helvetica', size=10)

        self.bg_color = "#f5f5f5"
        self.section_bg = "#e8f4f8"
        self.root.configure(bg=self.bg_color)

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Enter Human Gene Name:", font=self.normal_font).pack(side=tk.LEFT)

        self.gene_entry = ttk.Entry(search_frame, width=30, font=self.normal_font)
        self.gene_entry.pack(side=tk.LEFT, padx=10)
        self.gene_entry.bind('<Return>', lambda event: self.fetch_gene_info())
        self.gene_entry.focus_set()

        search_btn = ttk.Button(search_frame, text="Search", command=self.fetch_gene_info)
        search_btn.pack(side=tk.LEFT)

        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(results_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X)

    def fetch_gene_info(self):
        gene_name = self.gene_entry.get().strip().upper()
        if not gene_name:
            return

        self.status_var.set(f"Searching for {gene_name}...")
        self.root.update_idletasks()

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term={gene_name}[gene]+AND+homo+sapiens[orgn]&retmode=json"
            search_response = self.send_get_request(search_url)
            search_json = json.loads(search_response)

            if not search_json["esearchresult"]["idlist"]:
                messagebox.showerror("Error", f"No human gene found with name: {gene_name}")
                self.status_var.set("Ready")
                return

            gene_id = search_json["esearchresult"]["idlist"][0]

            summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id={gene_id}&retmode=json"
            summary_response = self.send_get_request(summary_url)
            summary_json = json.loads(summary_response)
            gene_data = summary_json["result"][gene_id]

            gene_symbol = gene_data.get("name", gene_name)
            kegg_gene_id = f"hsa:{gene_symbol}"

            kegg_url = f"http://rest.kegg.jp/get/{kegg_gene_id}"
            kegg_response = self.send_get_request(kegg_url)

            kegg_data = self.parse_kegg_response(kegg_response)
            ncbi_name = gene_data.get("description", "N/A")
            ncbi_function = gene_data.get("summary", "N/A")

            row = 0

            header_frame = ttk.Frame(self.scrollable_frame, padding=(10, 5), relief=tk.RAISED, borderwidth=1)
            header_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
            ttk.Label(header_frame, text=f"GENE INFORMATION: {gene_name}", font=self.title_font).pack()
            row += 1

            info_frame = ttk.Frame(self.scrollable_frame, padding=(10, 5))
            info_frame.grid(row=row, column=0, sticky="ew")
            ttk.Label(info_frame, text=f"NCBI Gene ID: {gene_id}", font=self.normal_font).grid(row=0, column=0, sticky="w")
            ttk.Label(info_frame, text=f"KEGG ID: {kegg_gene_id}", font=self.normal_font).grid(row=1, column=0, sticky="w", pady=(5, 0))
            row += 1

            full_name = self.get_full_name(kegg_data, ncbi_name)
            name_frame = ttk.LabelFrame(self.scrollable_frame, text="Full Name", padding=10)
            name_frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))
            ttk.Label(name_frame, text=full_name, font=self.normal_font, wraplength=800).pack(anchor="w")
            row += 1

            func_frame = ttk.LabelFrame(self.scrollable_frame, text="Biological Function", padding=10)
            func_frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))
            ttk.Label(func_frame, text=ncbi_function, font=self.normal_font, wraplength=800).pack(anchor="w")
            row += 1

            if 'ORTHOLOGY' in kegg_data:
                ortho_frame = ttk.LabelFrame(self.scrollable_frame, text="Orthology", padding=10)
                ortho_frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))

                orthology_text = kegg_data['ORTHOLOGY']
                orthology_trimmed = orthology_text[7:] if len(orthology_text) > 7 else ""
                ttk.Label(ortho_frame, text=orthology_text, font=self.normal_font, wraplength=800).pack(anchor="w")

                pdb_code = self.cauta_proteina(orthology_trimmed)
                if pdb_code != "N/A":
                    def show_embedded_structure():
                        url = f"https://www.rcsb.org/3d-view/{pdb_code}"
                        webview.create_window(f"3D Structure Viewer: {pdb_code}", url, width=900, height=700)
                        webview.start()

                    ttk.Label(ortho_frame, text=f"PDB Code: {pdb_code}", font=self.normal_font, foreground="blue").pack(anchor="w", pady=(5, 0))
                    ttk.Button(ortho_frame, text="View 3D Structure", command=show_embedded_structure).pack(anchor="w")
                row += 1

            if 'PATHWAY' in kegg_data:
                path_frame = ttk.LabelFrame(self.scrollable_frame, text="Pathways", padding=10)
                path_frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))
                pathways = kegg_data['PATHWAY']
                if pathways != "N/A":
                    pathways = pathways.split('hsa')
                    for pathway in pathways[1:]:
                        path_text = f"hsa{pathway.strip()}"
                        ttk.Label(path_frame, text=path_text, font=self.normal_font).pack(anchor="w", pady=(0, 3))
                row += 1

            if 'DISEASE' in kegg_data:
                disease_frame = ttk.LabelFrame(self.scrollable_frame, text="Disease Associations", padding=10)
                disease_frame.grid(row=row, column=0, sticky="ew", pady=(10, 0))

                diseases = kegg_data['DISEASE']
                if diseases != "N/A":
                    disease_list = [d.strip() for d in diseases.split('H') if d.strip()]
                    for i, disease in enumerate(disease_list):
                        disease_text = f"H{disease}" if i == 0 and not disease.startswith('0') else (
                            f"H{disease}" if disease[0].isdigit() else disease)

                        d_frame = ttk.Frame(disease_frame)
                        d_frame.pack(fill=tk.X, pady=(0, 5))

                        parts = disease_text.split('  ', 1)
                        if len(parts) == 2:
                            code, desc = parts
                            ttk.Label(d_frame, text=code, font=self.normal_font, width=10).pack(side=tk.LEFT, anchor="w")
                            ttk.Label(d_frame, text=desc, font=self.normal_font, wraplength=700).pack(side=tk.LEFT, anchor="w")
                        else:
                            ttk.Label(d_frame, text=disease_text, font=self.normal_font).pack(anchor="w")
                row += 1

            self.status_var.set(f"Found information for {gene_name}")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Could not connect to services: {str(e)}")
            self.status_var.set("Network error occurred")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Error occurred")

        self.scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_full_name(self, kegg_data, ncbi_name):
        if 'ORTHOLOGY' in kegg_data:
            ko_entry = kegg_data['ORTHOLOGY']
            if '[' in ko_entry:
                return ko_entry.split('[')[0].strip()

        if 'NAME' in kegg_data:
            return kegg_data['NAME']

        if 'DEFINITION' in kegg_data:
            return kegg_data['DEFINITION']

        return ncbi_name

    def send_get_request(self, url_string):
        response = requests.get(url_string)
        response.raise_for_status()
        return response.text

    def parse_kegg_response(self, text):
        result = {}
        current_section = None
        current_content = ""

        for line in text.split('\n'):
            if not line.strip():
                continue

            if line[0].isupper() and line[0] != ' ':
                if current_section:
                    result[current_section] = current_content.strip()

                section_end = line.find('  ')
                if section_end > 0:
                    current_section = line[:section_end].strip()
                    current_content = line[section_end:].strip()
                else:
                    current_section = line.strip()
                    current_content = ""
                continue

            if current_section and line.startswith('    '):
                current_content += " " + line.strip()

        if current_section:
            result[current_section] = current_content.strip()

        return result

    def cauta_proteina(self, protein_name):
        url = "https://search.rcsb.org/rcsbsearch/v2/query"

        query = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "struct.title",
                    "operator": "contains_words",
                    "value": protein_name
                }
            },
            "return_type": "entry",
            "request_options": {
                "results_content_type": ["experimental"],
                "paginate": {
                    "start": 0,
                    "rows": 1
                }
            }
        }

        response = requests.post(url, json=query)

        if response.status_code == 200:
            data = response.json()
            try:
                return data['result_set'][0]['identifier']
            except (IndexError, KeyError):
                return "N/A"
        else:
            return "N/A"


if __name__ == "__main__":
    root = tk.Tk()
    app = GeneInfoApp(root)
    root.mainloop()