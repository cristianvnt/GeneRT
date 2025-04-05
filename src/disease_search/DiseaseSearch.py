import requests
import re
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
from bs4 import BeautifulSoup


class DiseaseGeneApp:
    def __init__(self, root):
        self.root = root
        root.title("KEGG Disease Gene Drug Explorer")
        root.geometry("1200x800")

        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('TLabel', background='#f5f5f5', font=('Helvetica', 10))
        self.style.configure('Title.TLabel', font=('Helvetica', 14, 'bold'))
        self.style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('TButton', font=('Helvetica', 10))

        # Create UI
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Search panel
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=10)

        ttk.Label(search_frame, text="Disease Name:", style='Title.TLabel').pack(side=tk.LEFT)

        self.disease_entry = ttk.Entry(search_frame, width=40)
        self.disease_entry.pack(side=tk.LEFT, padx=10)
        self.disease_entry.bind('<Return>', lambda e: self.search_disease())

        search_btn = ttk.Button(search_frame, text="Search by Name", command=self.search_disease)
        search_btn.pack(side=tk.LEFT, padx=5)

        # Direct ID lookup
        ttk.Label(search_frame, text="  Disease ID:", style='Title.TLabel').pack(side=tk.LEFT, padx=(20, 0))

        self.id_entry = ttk.Entry(search_frame, width=15)
        self.id_entry.pack(side=tk.LEFT, padx=10)
        self.id_entry.bind('<Return>', lambda e: self.lookup_disease_id())

        id_btn = ttk.Button(search_frame, text="Lookup ID", command=self.lookup_disease_id)
        id_btn.pack(side=tk.LEFT)

        # Results notebook with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Tab 1: Search Results
        self.search_results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_results_frame, text="Search Results")

        # Treeview for search results
        self.results_tree = ttk.Treeview(self.search_results_frame,
                                         columns=('disease_id', 'disease_name'),
                                         show='headings')
        self.results_tree.heading('disease_id', text='Disease ID')
        self.results_tree.heading('disease_name', text='Disease Name')

        # Configure column widths
        self.results_tree.column('disease_id', width=100)
        self.results_tree.column('disease_name', width=400)

        # Add scrollbar
        results_scrollbar = ttk.Scrollbar(self.search_results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)

        # Pack search results widgets
        self.results_tree.pack(side="left", fill="both", expand=True)
        results_scrollbar.pack(side="right", fill="y")

        # Bind double-click to load disease details
        self.results_tree.bind("<Double-1>", self.on_result_double_click)

        # Tab 2: Disease Details
        self.disease_details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.disease_details_frame, text="Disease Details")

        # Create a frame for basic disease info
        basic_info_frame = ttk.Frame(self.disease_details_frame)
        basic_info_frame.pack(fill=tk.X, pady=5)

        # Disease details labels
        self.disease_name_var = tk.StringVar()
        self.disease_id_var = tk.StringVar()
        self.category_var = tk.StringVar()

        # First row: Name and ID
        ttk.Label(basic_info_frame, text="Name:", style='Header.TLabel').grid(row=0, column=0, sticky='w', padx=5)
        ttk.Label(basic_info_frame, textvariable=self.disease_name_var).grid(row=0, column=1, sticky='w', padx=5)

        ttk.Label(basic_info_frame, text="ID:", style='Header.TLabel').grid(row=0, column=2, sticky='w', padx=5)
        ttk.Label(basic_info_frame, textvariable=self.disease_id_var).grid(row=0, column=3, sticky='w', padx=5)

        # Second row: Category
        ttk.Label(basic_info_frame, text="Category:", style='Header.TLabel').grid(row=1, column=0, sticky='w', padx=5)
        ttk.Label(basic_info_frame, textvariable=self.category_var).grid(row=1, column=1, sticky='w', columnspan=3,
                                                                         padx=5)

        # Description section
        desc_frame = ttk.LabelFrame(self.disease_details_frame, text="Description")
        desc_frame.pack(fill=tk.X, pady=5, padx=5)

        self.description_text = tk.Text(desc_frame, wrap=tk.WORD, height=4, width=50)
        self.description_text.pack(fill=tk.X, padx=5, pady=5)
        self.description_text.config(state=tk.DISABLED)

        # Create notebook for pathways, genes, and drugs
        details_notebook = ttk.Notebook(self.disease_details_frame)
        details_notebook.pack(fill=tk.BOTH, expand=True, pady=5)

        # Pathways tab
        pathways_frame = ttk.Frame(details_notebook)
        details_notebook.add(pathways_frame, text="Pathways")

        # Pathways treeview
        self.pathways_tree = ttk.Treeview(pathways_frame, columns=('id', 'name'), show='headings')
        self.pathways_tree.heading('id', text='Pathway ID')
        self.pathways_tree.heading('name', text='Pathway Name')
        self.pathways_tree.column('id', width=100)
        self.pathways_tree.column('name', width=400)

        pathways_scrollbar = ttk.Scrollbar(pathways_frame, orient="vertical", command=self.pathways_tree.yview)
        self.pathways_tree.configure(yscrollcommand=pathways_scrollbar.set)

        self.pathways_tree.pack(side="left", fill="both", expand=True)
        pathways_scrollbar.pack(side="right", fill="y")

        # Genes tab
        genes_frame = ttk.Frame(details_notebook)
        details_notebook.add(genes_frame, text="Genes")

        # Genes treeview
        self.genes_tree = ttk.Treeview(genes_frame,
                                       columns=('name', 'detail', 'hsa', 'ko'),
                                       show='headings')
        self.genes_tree.heading('name', text='Gene Name')
        self.genes_tree.heading('detail', text='Details')
        self.genes_tree.heading('hsa', text='HSA ID')
        self.genes_tree.heading('ko', text='KO ID')

        self.genes_tree.column('name', width=150)
        self.genes_tree.column('detail', width=250)
        self.genes_tree.column('hsa', width=100)
        self.genes_tree.column('ko', width=100)

        genes_scrollbar = ttk.Scrollbar(genes_frame, orient="vertical", command=self.genes_tree.yview)
        self.genes_tree.configure(yscrollcommand=genes_scrollbar.set)

        self.genes_tree.pack(side="left", fill="both", expand=True)
        genes_scrollbar.pack(side="right", fill="y")

        # Drugs tab (new)
        drugs_frame = ttk.Frame(details_notebook)
        details_notebook.add(drugs_frame, text="Drugs")

        # Drugs treeview with updated columns
        self.drugs_tree = ttk.Treeview(drugs_frame,
                                       columns=('id', 'name'),
                                       show='headings')
        self.drugs_tree.heading('id', text='Drug ID')
        self.drugs_tree.heading('name', text='Drug Name')

        self.drugs_tree.column('id', width=100)
        self.drugs_tree.column('name', width=200)

        drugs_scrollbar = ttk.Scrollbar(drugs_frame, orient="vertical", command=self.drugs_tree.yview)
        self.drugs_tree.configure(yscrollcommand=drugs_scrollbar.set)

        self.drugs_tree.pack(side="left", fill="both", expand=True)
        drugs_scrollbar.pack(side="right", fill="y")

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X)

    def search_disease(self):
        """Search for a disease by name in the KEGG database"""
        disease_name = self.disease_entry.get().strip()
        if not disease_name:
            messagebox.showwarning("Input Error", "Please enter a disease name")
            return

        self.status_var.set(f"Searching for {disease_name}...")
        self.root.update()

        try:
            # Clear previous results
            self.results_tree.delete(*self.results_tree.get_children())

            # Search KEGG via REST API
            search_url = f'https://rest.kegg.jp/find/disease/{disease_name}'
            response = requests.get(search_url)

            if response.status_code != 200:
                messagebox.showerror("Error", f"Search failed with status code: {response.status_code}")
                self.status_var.set("Search failed")
                return

            # Parse and display results
            results = []
            for line in response.text.strip().split('\n'):
                if not line.strip():
                    continue

                parts = line.split('\t')
                if len(parts) >= 2:
                    disease_id = parts[0]
                    disease_desc = parts[1]
                    results.append((disease_id, disease_desc))

                    # Add to treeview
                    self.results_tree.insert('', 'end', values=(disease_id, disease_desc))

            if not results:
                messagebox.showinfo("No Results", f"No diseases found matching '{disease_name}'")
                self.status_var.set("No results found")
            else:
                self.status_var.set(f"Found {len(results)} results for '{disease_name}'")
                # Switch to results tab
                self.notebook.select(0)  # Select the search results tab

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Error occurred")

    def lookup_disease_id(self):
        """Look up a disease directly by ID"""
        disease_id = self.id_entry.get().strip()
        if not disease_id:
            messagebox.showwarning("Input Error", "Please enter a disease ID")
            return

        self.display_disease_details(disease_id)

    def on_result_double_click(self, event):
        """Handle double-click on a search result to show details"""
        selected_item = self.results_tree.selection()
        if not selected_item:
            return

        # Get the disease ID from the selected item
        disease_id = self.results_tree.item(selected_item[0], 'values')[0]
        self.display_disease_details(disease_id)

    def display_disease_details(self, disease_id):
        """Display detailed information about a disease"""
        self.status_var.set(f"Loading details for {disease_id}...")
        self.root.update()

        try:
            # Fetch disease data
            disease_data = self.get_kegg_disease(disease_id)

            if not disease_data:
                messagebox.showerror("Error", f"Could not retrieve details for {disease_id}")
                self.status_var.set("Data retrieval failed")
                return

            # Update the UI with disease details
            self.update_disease_details_ui(disease_data)

            # Fetch and display drug information
            disease_name = disease_data["name"]
            self.fetch_drug_info(disease_name, disease_id)

            # Switch to the details tab
            self.notebook.select(1)  # Select the disease details tab
            self.status_var.set(f"Loaded details for {disease_id}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set("Error occurred")

    def update_disease_details_ui(self, disease_data):
        """Update the UI with disease details"""
        # Update basic info
        self.disease_name_var.set(disease_data["name"])
        self.disease_id_var.set(disease_data["entry"])
        self.category_var.set(disease_data["category"])

        # Update description
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, disease_data["description"])
        self.description_text.config(state=tk.DISABLED)

        # Update pathways
        self.pathways_tree.delete(*self.pathways_tree.get_children())
        for pathway in disease_data["pathways"]:
            self.pathways_tree.insert('', 'end', values=(pathway["id"], pathway["name"]))

        # Update genes
        self.genes_tree.delete(*self.genes_tree.get_children())
        for gene in disease_data["genes"]:
            self.genes_tree.insert('', 'end', values=(
                gene["name"],
                gene["detail"],
                f"HSA:{gene['hsa']}" if gene['hsa'] else "",
                f"KO:{gene['ko']}" if gene['ko'] else ""
            ))

    def fetch_drug_info(self, disease_name, disease_id):
        """Fetch drug information for a disease from KEGG"""
        self.status_var.set(f"Fetching drug information for {disease_name}...")
        self.root.update()

        try:
            # Clear previous drug results
            self.drugs_tree.delete(*self.drugs_tree.get_children())

            # Construct the drug search URL
            search_url = f"https://www.kegg.jp/kegg-bin/search?from=disease&q={disease_name.replace(' ', '+')}&display=drug&search_gene=1&target=compound%2bdrug%2bdgroup%2bdisease"
            response = requests.get(search_url)

            if response.status_code != 200:
                self.status_var.set(f"Failed to fetch drug information (Status: {response.status_code})")
                return

            drugs = self.parse_drugs_from_html(response.text, disease_name, disease_id)

            for drug in drugs:
                self.drugs_tree.insert('', 'end', values=(drug["drug_id"], drug["name"]))

            self.status_var.set(f"Found {len(drugs)} drugs for {disease_name}")

        except Exception as e:
            self.status_var.set(f"Error fetching drug information: {str(e)}")
            print(f"Drug fetch error: {str(e)}")

    def parse_drugs_from_html(self, html_text, disease_name, disease_id):
        """Parse drug info from KEGG drug search HTML result"""
        soup = BeautifulSoup(html_text, 'html.parser')
        drug_table = soup.find("table", class_="list1")
        if not drug_table:
            return []

        target_disease_ids = [disease_id]
        if ":" not in disease_id:
            target_disease_ids.append(f"DS:{disease_id}")

        drugs = []
        rows = drug_table.find_all("tr")[1:]  # Skip header row

        for row in rows:
            try:
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue

                drug_id = cols[0].text.strip()
                drug_name = cols[1].text.strip()

                # Optional: Parse the diseases column to make sure it's linked to our disease
                diseases_text = cols[3].text.strip()
                matched = any(disease_name.lower() in diseases_text.lower() or t_id in diseases_text for t_id in
                              target_disease_ids)

                if matched:
                    drugs.append({
                        "drug_id": drug_id,
                        "name": drug_name
                    })

            except Exception as e:
                print(f"Error parsing row: {e}")

        return drugs

    def get_kegg_disease(self, disease_id):
        """
        Retrieve detailed information about a specific disease from KEGG using its ID.

        Args:
            disease_id (str): The KEGG disease ID (e.g., H00026)

        Returns:
            dict: A dictionary containing parsed disease information
        """
        url = f'https://rest.kegg.jp/get/{disease_id}'
        response = requests.get(url)

        if response.status_code != 200:
            print(f'Error retrieving disease details: {response.status_code}')
            return None

        # Initialize data structure
        disease_data = {
            "entry": "",
            "name": "",
            "description": "",
            "category": "",
            "pathways": [],
            "genes": []
        }

        # Track current section and collect multiline content
        current_section = None
        section_content = []

        # Process each line
        lines = response.text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Check for section headers (not indented)
            if not line.startswith(" "):
                # Process the previous section content if any
                if current_section and section_content:
                    self.process_section(disease_data, current_section, section_content)
                    section_content = []

                # Set new section
                if " " in line:
                    current_section = line.split(" ")[0]
                    # Handle section header that also contains content
                    content = line[len(current_section):].strip()
                    if content:
                        section_content.append(content)
                else:
                    current_section = line.strip()
            else:
                # Add content to current section
                section_content.append(line.strip())

            i += 1

        # Process the last section
        if current_section and section_content:
            self.process_section(disease_data, current_section, section_content)

        return disease_data

    def process_section(self, disease_data, section, content):
        """
        Process a section of the KEGG response and update the disease_data dictionary.

        Args:
            disease_data (dict): The dictionary to update
            section (str): The section name (e.g., 'ENTRY', 'GENE')
            content (list): List of content lines for this section
        """
        combined_content = " ".join(content)

        if section == "ENTRY":
            disease_data["entry"] = content[0].split()[0]

        elif section == "NAME":
            disease_data["name"] = combined_content

        elif section == "DESCRIPTION":
            disease_data["description"] = combined_content

        elif section == "CATEGORY":
            disease_data["category"] = combined_content

        elif section == "PATHWAY":
            for line in content:
                # Extract pathway ID and name
                match = re.search(r'(hsa\d+)\s+(.*)', line)
                if match:
                    pathway_id, pathway_name = match.groups()
                    disease_data["pathways"].append({
                        "id": pathway_id,
                        "name": pathway_name
                    })

        elif section == "GENE":
            # Handle gene information with various formats
            for line in content:
                # Try different patterns to match complex gene data
                gene_name = gene_detail = hsa_id = ko_id = ""

                # Pattern 1: Full format with detail (e.g. "GENE1 (mutation) [HSA:1234] [KO:K5678]")
                pattern1 = re.search(r'([^\[]+?)(?:\s+\(([^)]+)\))?\s+\[HSA:(\d+)\](?:\s+\[KO:([^\]]+)\])?', line)
                if pattern1:
                    gene_name = pattern1.group(1).strip()
                    gene_detail = pattern1.group(2).strip() if pattern1.group(2) else ""
                    hsa_id = pattern1.group(3).strip() if pattern1.group(3) else ""
                    ko_id = pattern1.group(4).strip() if pattern1.group(4) else ""
                else:
                    # Pattern 2: Name with HSA but no detail (e.g. "GENE1 [HSA:1234]")
                    pattern2 = re.search(r'([^\[]+?)\s+\[HSA:(\d+)\]', line)
                    if pattern2:
                        gene_name = pattern2.group(1).strip()
                        hsa_id = pattern2.group(2).strip()

                        # Check for KO after HSA
                        ko_match = re.search(r'\[KO:([^\]]+)\]', line)
                        if ko_match:
                            ko_id = ko_match.group(1).strip()

                # If we found a gene name, add it to our list
                if gene_name:
                    disease_data["genes"].append({
                        "name": gene_name,
                        "detail": gene_detail,
                        "hsa": hsa_id,
                        "ko": ko_id
                    })


def main():
    root = tk.Tk()
    app = DiseaseGeneApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()