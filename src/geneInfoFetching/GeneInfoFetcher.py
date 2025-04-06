import requests
import json
import tkinter as tk
from tkinter import messagebox
from tkinter.font import Font
import webbrowser

import webview

from src.geneInfoFetching.GeneGraph import GeneNetworkViewer

class GeneInfoApp:
    def __init__(self, root):
        self.root = root

        self.title_font = Font(family='Helvetica', size=14, weight='bold')
        self.header_font = Font(family='Helvetica', size=12, weight='bold')
        self.normal_font = Font(family='Helvetica', size=10)

        self.create_widgets()

    def create_widgets(self):
        self.root.configure(bg=self.root["bg"])

        main_frame = tk.Frame(self.root, bg=self.root["bg"], padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        search_frame = tk.Frame(main_frame, bg=self.root["bg"])
        search_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(search_frame, text="Enter Human Gene Name:", font=self.normal_font, bg=self.root["bg"]).pack(side=tk.LEFT)

        self.gene_entry = tk.Entry(search_frame, width=30, font=self.normal_font, bg="white")
        self.gene_entry.pack(side=tk.LEFT, padx=10)
        self.gene_entry.bind('<Return>', lambda event: self.fetch_gene_info())
        self.gene_entry.focus_set()

        search_btn = tk.Button(search_frame, text="Search", command=self.fetch_gene_info)
        search_btn.pack(side=tk.LEFT)

        results_frame = tk.Frame(main_frame, bg=self.root["bg"])
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(results_frame, bg=self.root["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.root["bg"], padx=20, pady=10)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def fetch_gene_info(self):
        gene_name = self.gene_entry.get().strip().upper()
        if not gene_name:
            return

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gene&term={gene_name}[gene]+AND+homo+sapiens[orgn]&retmode=json"
            search_response = self.send_get_request(search_url)
            search_json = json.loads(search_response)

            if not search_json["esearchresult"]["idlist"]:
                messagebox.showerror("Error", f"No human gene found with name: {gene_name}")
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

            self.add_section("Gene Information: {}".format(gene_name), [
                f"NCBI Gene ID: {gene_id}",
                f"KEGG ID: {kegg_gene_id}"
            ])

            self.add_section("Description", [
                f"Full Name: {self.get_full_name(kegg_data, ncbi_name)}",
                f"Function: {ncbi_function}"
            ])

            if 'ORTHOLOGY' in kegg_data:
                ortho_text = kegg_data['ORTHOLOGY']
                section_widgets = [ortho_text]

                protein_name = ortho_text[7:] if len(ortho_text) > 7 else ""
                pdb_code = self.cauta_proteina(protein_name)
                if pdb_code != "N/A":
                    section_widgets.append(f"3D Structure: {pdb_code}")

                section = self.add_section("Orthology", section_widgets)

                if pdb_code != "N/A":
                    btn = tk.Button(section, text=f"Open 3D Structure: {pdb_code}", font=self.normal_font, command=lambda: self.show_embedded_structure(pdb_code))
                    btn.pack(anchor="w", padx=20, pady=(5, 10))

            if 'PATHWAY' in kegg_data:
                pathways = [f"- hsa{path.strip()}" for path in kegg_data['PATHWAY'].split('hsa')[1:]]
                self.add_section("Pathways", pathways)

            if 'DISEASE' in kegg_data:
                diseases = [f"- H{line.strip()}" if line.strip() and line.strip()[0].isdigit() else f"- {line.strip()}"
                            for line in kegg_data['DISEASE'].split('H') if line.strip()]
                self.add_section("Disease Associations", diseases)


        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Could not connect to services: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

        self.scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def add_section(self, title, lines):
        section = tk.Frame(self.scrollable_frame, bg="#f9f9f9", bd=0, highlightbackground="#dddddd", highlightthickness=1)
        section.pack(fill="x", pady=10, padx=10, ipady=10, ipadx=10)

        container = tk.Frame(section, bg="#f9f9f9")
        container.pack(fill="x")

        tk.Label(container, text=title, font=self.header_font, bg="#f9f9f9", anchor="w").pack(fill="x", padx=10, pady=(5, 5))
        for line in lines:
            tk.Label(container, text=line, font=self.normal_font, bg="#f9f9f9", anchor="w", wraplength=700, justify="left").pack(fill="x", padx=20, pady=2)

        return section

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

    def get_full_name(self, kegg_data, ncbi_name):
        if 'ORTHOLOGY' in kegg_data:
            ko_entry = kegg_data['ORTHOLOGY']
            if '[' in ko_entry:
                return ko_entry.split('[')[0].strip()

        return kegg_data.get('NAME', kegg_data.get('DEFINITION', ncbi_name))

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
        return "N/A"

    def show_embedded_structure(self, pdb_code):
        url = f"https://www.rcsb.org/3d-view/{pdb_code}"
        webview.create_window(f"3D Structure Viewer: {pdb_code}", url, width=900, height=700)
        webview.start()

