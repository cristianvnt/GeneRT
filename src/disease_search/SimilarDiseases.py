
import requests
import re
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from functools import lru_cache
import threading
from queue import Queue

from bs4 import BeautifulSoup


class DiseaseGeneApp:
    def __init__(self, root):
        self.root = root
        frame = tk.Frame(root, bg="lightgreen")
        frame.pack(fill="both", expand=True)

        label = tk.Label(frame, text="Similar Diseases Component", bg="lightgreen", font=("Arial", 14))
        label.pack(pady=20)

        # Configuration - Default Settings
        self.max_diseases_to_check = 200  # Limit number of diseases to check
        self.max_results = 50
        self.stop_comparison = False
        self.comparison_queue = Queue()

        # Caches
        self.pathway_cache = {}
        self.disease_cache = {}

        # UI Setup
        self.setup_ui()

    def setup_ui(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Search Panel
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=10)

        ttk.Label(search_frame, text="Disease ID/Name:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        search_btn = ttk.Button(search_frame, text="Search", command=self.search_disease)
        search_btn.pack(side=tk.LEFT)

        compare_btn = ttk.Button(search_frame, text="Find Similar", command=self.start_comparison)
        compare_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = ttk.Button(search_frame, text="Stop", command=self.stop_comparison_operation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        # Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Disease Info Tab
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Disease Info")

        # Comparison Results Tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Similar Diseases")

        # Setup info and results widgets
        self.setup_info_tab()
        self.setup_results_tab()

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken")
        self.status_bar.pack(fill=tk.X)

        self.status_var.set("Ready")

    def setup_info_tab(self):
        # Disease information widgets
        ttk.Label(self.info_frame, text="Disease Information", font=('Arial', 12, 'bold')).pack(pady=5)

        info_frame = ttk.Frame(self.info_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(info_frame, text="ID:").grid(row=0, column=0, sticky="w")
        self.disease_id_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.disease_id_var).grid(row=0, column=1, sticky="w")

        ttk.Label(info_frame, text="Name:").grid(row=1, column=0, sticky="w")
        self.disease_name_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.disease_name_var).grid(row=1, column=1, sticky="w")

        ttk.Label(info_frame, text="Category:").grid(row=2, column=0, sticky="w")
        self.category_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.category_var).grid(row=2, column=1, sticky="w")

        # Pathways list
        pathways_frame = ttk.LabelFrame(self.info_frame, text="Associated Pathways")
        pathways_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.pathways_tree = ttk.Treeview(pathways_frame, columns=('id', 'name'), show='headings', height=10)
        self.pathways_tree.heading('id', text='Pathway ID')
        self.pathways_tree.heading('name', text='Pathway Name')
        self.pathways_tree.column('id', width=100)
        self.pathways_tree.column('name', width=800)

        scrollbar = ttk.Scrollbar(pathways_frame, orient="vertical", command=self.pathways_tree.yview)
        self.pathways_tree.configure(yscrollcommand=scrollbar.set)

        self.pathways_tree.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_results_tab(self):
        # Comparison results widgets
        self.results_tree = ttk.Treeview(self.results_frame,
                                         columns=('id', 'name', 'score'),
                                         show='headings',
                                         height=20)
        self.results_tree.heading('id', text='Disease ID')
        self.results_tree.heading('name', text='Disease Name')
        self.results_tree.heading('score', text='Similarity')

        self.results_tree.column('id', width=100)
        self.results_tree.column('name', width=600)
        self.results_tree.column('score', width=80)

        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.results_tree.bind("<Double-1>", self.load_selected_disease)

    def search_disease(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a disease ID or name")
            return

        self.status_var.set(f"Searching for {query}...")
        self.root.update_idletasks()

        try:
            # Try to get disease directly if it looks like an ID
            if re.match(r'^[Hh]\d{5}$', query):
                disease_id = query.upper()
                disease_data = self.get_kegg_disease(disease_id)
                if disease_data:
                    self.display_disease(disease_data)
                    return
                else:
                    messagebox.showinfo("Not Found", f"Disease ID {disease_id} not found")
                    self.status_var.set("Ready")
                    return

            # Otherwise search by name
            response = requests.get(f'https://rest.kegg.jp/find/disease/{query}')
            if response.status_code == 200:
                diseases = []
                for line in response.text.split('\n'):
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            diseases.append((parts[0], parts[1]))

                if len(diseases) == 1:
                    disease_data = self.get_kegg_disease(diseases[0][0])
                    self.display_disease(disease_data)
                elif len(diseases) > 1:
                    self.show_disease_selection(diseases)
                else:
                    messagebox.showinfo("Not Found", "No matching diseases found")
                    self.status_var.set("Ready")
            else:
                messagebox.showerror("Error", f"API request failed with status code {response.status_code}")
                self.status_var.set("Ready")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error occurred during search")

    def show_disease_selection(self, diseases):
        # Create selection dialog
        select_win = tk.Toplevel(self.root)
        select_win.title("Select Disease")
        select_win.geometry("500x400")
        select_win.transient(self.root)
        select_win.grab_set()

        ttk.Label(select_win, text="Multiple diseases found. Please select one:",
                  font=('Arial', 10)).pack(pady=5)

        # Create frame for treeview and scrollbar
        tree_frame = ttk.Frame(select_win)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create treeview
        tree = ttk.Treeview(tree_frame, columns=('id', 'name'), show='headings')
        tree.heading('id', text='ID')
        tree.heading('name', text='Name')
        tree.column('id', width=100)
        tree.column('name', width=350)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

        # Populate treeview
        for disease_id, disease_name in diseases:
            tree.insert('', 'end', values=(disease_id, disease_name))

        button_frame = ttk.Frame(select_win)
        button_frame.pack(fill=tk.X, pady=10)

        def on_select():
            selected = tree.selection()
            if selected:
                disease_id = tree.item(selected[0], 'values')[0]
                select_win.destroy()

                self.status_var.set(f"Loading disease {disease_id}...")
                self.root.update_idletasks()

                disease_data = self.get_kegg_disease(disease_id)
                if disease_data:
                    self.display_disease(disease_data)
                else:
                    messagebox.showerror("Error", f"Failed to load disease {disease_id}")
                    self.status_var.set("Ready")
            else:
                messagebox.showwarning("Warning", "Please select a disease")

        def on_cancel():
            select_win.destroy()
            self.status_var.set("Ready")

        ttk.Button(button_frame, text="Select", command=on_select).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=10)

        # Double-click to select
        tree.bind("<Double-1>", lambda e: on_select())

    def get_kegg_disease(self, disease_id):
        if disease_id in self.disease_cache:
            return self.disease_cache[disease_id]

        try:
            response = requests.get(f'https://rest.kegg.jp/get/{disease_id}')
            if response.status_code == 200 and response.text.strip():
                disease_data = {'entry': disease_id, 'pathways': []}
                current_section = None
                buffer = ""

                for line in response.text.split('\n'):
                    if not line.strip():
                        continue

                    # Detect start of new section
                    if not line.startswith(' '):
                        if current_section == 'PATHWAY' and buffer:
                            # Process any buffered pathway content
                            for pathway_match in re.finditer(r'(hsa\d+)\s+(.+?)(?=hsa\d+|\Z)', buffer):
                                disease_data['pathways'].append({
                                    'id': pathway_match.group(1),
                                    'name': pathway_match.group(2).strip()
                                })
                            buffer = ""

                        section = line[:12].strip()
                        content = line[12:].strip()
                        current_section = section

                        if section == 'ENTRY':
                            disease_data['entry'] = content.split()[0]
                        elif section == 'NAME':
                            disease_data['name'] = content
                        elif section == 'CATEGORY':
                            disease_data['category'] = content
                        elif section == 'DESCRIPTION':
                            disease_data['description'] = content
                        elif section == 'PATHWAY':
                            buffer = content
                    else:
                        content = line.strip()
                        if current_section == 'PATHWAY':
                            buffer += " " + content

                # Final check for last buffer
                if current_section == 'PATHWAY' and buffer:
                    for pathway_match in re.finditer(r'(hsa\d+)\s+(.+?)(?=hsa\d+|\Z)', buffer):
                        disease_data['pathways'].append({
                            'id': pathway_match.group(1),
                            'name': pathway_match.group(2).strip()
                        })

                # If no pathways found using the regex pattern, try alternative parsing
                if not disease_data['pathways'] and buffer:
                    parts = buffer.split('hsa')
                    for part in parts[1:]:  # Skip first empty part
                        if part.strip():
                            pathway_id = 'hsa' + part.split()[0]
                            pathway_name = ' '.join(part.split()[1:])
                            disease_data['pathways'].append({
                                'id': pathway_id,
                                'name': pathway_name
                            })

                self.disease_cache[disease_id] = disease_data
                return disease_data
            elif response.status_code != 200:
                self.status_var.set(f"Error: API returned status code {response.status_code}")
                return None
            else:
                self.status_var.set(f"Error: No data returned for {disease_id}")
                return None

        except Exception as e:
            self.status_var.set(f"Error fetching disease data: {str(e)}")
            return None

    def display_disease(self, disease_data):
        if not disease_data:
            messagebox.showerror("Error", "No disease data to display")
            return

        self.disease_id_var.set(disease_data.get('entry', ''))
        self.disease_name_var.set(disease_data.get('name', ''))
        self.category_var.set(disease_data.get('category', ''))

        self.pathways_tree.delete(*self.pathways_tree.get_children())
        for pathway in disease_data.get('pathways', []):
            self.pathways_tree.insert('', 'end', values=(pathway['id'], pathway['name']))

        self.status_var.set(f"Loaded {disease_data.get('name', '')}")
        self.notebook.select(0)  # Switch to disease info tab

    def start_comparison(self):
        disease_id = self.disease_id_var.get()
        if not disease_id:
            messagebox.showwarning("Warning", "No disease selected. Please search for a disease first.")
            return

        self.stop_comparison = False
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.pack(fill=tk.X, before=self.status_bar)
        self.progress['value'] = 0

        # Clear previous results
        self.results_tree.delete(*self.results_tree.get_children())

        threading.Thread(
            target=self.find_similar_diseases,
            args=(disease_id,),
            daemon=True
        ).start()

        self.check_comparison_progress()

    def stop_comparison_operation(self):
        self.stop_comparison = True
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Comparison stopped by user")

    @lru_cache(maxsize=200)
    def get_pathways(self, disease_id):
        """Get pathway IDs for a disease"""
        disease_data = self.get_kegg_disease(disease_id)
        return {p['id'] for p in disease_data.get('pathways', [])} if disease_data else set()

    def calculate_similarity(self, pathways1, pathways2):
        """Calculate Jaccard similarity between two sets of pathways"""
        if not pathways1 or not pathways2:
            return 0.0


        intersection = len(pathways1 & pathways2)
        union = len(pathways1 | pathways2)
        return intersection / union if union > 0 else 0.0

    def find_similar_diseases(self, start_id):
        try:
            # Get initial disease pathways
            start_pathways = self.get_pathways(start_id)
            if not start_pathways:
                self.comparison_queue.put(('error', "No pathways found for starting disease"))
                return

            # Get diseases for comparison - limited number for better performance
            self.comparison_queue.put(('status', "Loading disease database..."))
            all_diseases = self.get_all_diseases(limit=self.max_diseases_to_check)

            if not all_diseases:
                self.comparison_queue.put(('error', "Failed to retrieve disease database"))
                return

            self.comparison_queue.put(('status', f"Comparing with {len(all_diseases)} diseases..."))

            # Direct comparison approach - compare with all diseases in the limited set
            results = []

            for i, (disease_id, disease_name) in enumerate(all_diseases):
                if self.stop_comparison:
                    break

                # Skip self-comparison
                if disease_id == start_id:
                    continue

                other_pathways = self.get_pathways(disease_id)
                if not other_pathways:
                    continue

                score = self.calculate_similarity(start_pathways, other_pathways)

                # Only include if there's any similarity at all
                if score > 0:
                    results.append({
                        'id': disease_id,
                        'name': disease_name,
                        'score': score
                    })

                # Update progress periodically
                if i % 5 == 0:
                    progress = min(95, int((i / len(all_diseases)) * 100))
                    self.comparison_queue.put(('progress', progress))
                    self.comparison_queue.put(('status', f"Comparing diseases: {i}/{len(all_diseases)}"))

            # Sort by similarity score (descending)
            results.sort(key=lambda x: -x['score'])

            # Take top results
            final_results = results[:self.max_results]
            self.comparison_queue.put(('results', final_results))

        except Exception as e:
            self.comparison_queue.put(('error', f"Error during comparison: {str(e)}"))

    def get_all_diseases(self, limit=200):
        """Get limited number of diseases from KEGG database"""
        try:
            response = requests.get('https://rest.kegg.jp/list/disease')
            if response.status_code == 200:
                diseases = []
                for line in response.text.split('\n'):
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            diseases.append((parts[0], parts[1]))
                            if len(diseases) >= limit:
                                break
                return diseases
            else:
                return []
        except Exception as e:
            self.comparison_queue.put(('status', f"Error retrieving disease list: {str(e)}"))
            return []

    def check_comparison_progress(self):
        try:
            while not self.comparison_queue.empty():
                task_type, data = self.comparison_queue.get_nowait()

                if task_type == 'progress':
                    self.progress['value'] = data
                elif task_type == 'status':
                    self.status_var.set(data)
                elif task_type == 'results':
                    self.show_results(data)
                    self.progress.pack_forget()
                    self.stop_btn.config(state=tk.DISABLED)
                    return
                elif task_type == 'error':
                    messagebox.showerror("Error", data)
                    self.progress.pack_forget()
                    self.stop_btn.config(state=tk.DISABLED)
                    self.status_var.set("Error during comparison")
                    return

            if not self.stop_comparison:
                self.root.after(100, self.check_comparison_progress)
            else:
                self.progress.pack_forget()
                self.stop_btn.config(state=tk.DISABLED)
        except Exception as e:
            self.status_var.set(f"Error in progress monitoring: {str(e)}")
            self.progress.pack_forget()

    def show_results(self, results):
        # Șterge orice rezultat anterior
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Scrolleable canvas
        canvas = tk.Canvas(self.results_frame)
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.status_var.set("Loading drugs for similar diseases...")

        for result in results:
            disease_id = result['id']
            disease_name = result['name']
            score = result['score']

            # Frame pentru boală
            disease_frame = ttk.LabelFrame(scrollable_frame, text=f"{disease_name} (Similarity: {score:.2f})")
            disease_frame.pack(fill="x", expand=True, padx=10, pady=5)

            drug_label = ttk.Label(disease_frame, text="Drugs:")
            drug_label.pack(side="left", padx=(10, 5))

            drug_combo = ttk.Combobox(disease_frame, width=80)
            drug_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))

            # Fetch medicamente pentru fiecare boală (thread separat)
            threading.Thread(
                target=lambda combo=drug_combo, dname=disease_name, did=disease_id: self.populate_drug_combobox(combo,
                                                                                                                dname,
                                                                                                                did),
                daemon=True
            ).start()

        self.status_var.set(f"Found {len(results)} similar diseases")
        self.notebook.select(1)

    def populate_drug_combobox(self, combobox, disease_name, disease_id):
        try:
            url = f"https://www.kegg.jp/kegg-bin/search?from=disease&q={disease_name.replace(' ', '+')}&display=drug&search_gene=1&target=compound%2bdrug%2bdgroup%2bdisease"
            response = requests.get(url)

            if response.status_code != 200:
                return

            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            drug_table = soup.find("table", class_="list1")

            if not drug_table:
                return

            target_disease_ids = [disease_id]
            if ":" not in disease_id:
                target_disease_ids.append(f"DS:{disease_id}")

            drugs = []
            rows = drug_table.find_all("tr")[1:]

            for row in rows:
                try:
                    cols = row.find_all("td")
                    if len(cols) < 4:
                        continue

                    drug_id = cols[0].text.strip()
                    drug_name = cols[1].text.strip()
                    diseases_text = cols[3].text.strip()

                    matched = any(disease_name.lower() in diseases_text.lower() or t_id in diseases_text for t_id in
                                  target_disease_ids)

                    if matched:
                        drugs.append(f"{drug_id} - {drug_name}")
                except:
                    continue

            if drugs:
                combobox['values'] = drugs
                combobox.set(drugs[0])
            else:
                combobox['values'] = ["No drugs found"]
                combobox.set("No drugs found")

        except Exception as e:
            print(f"Error fetching drugs for {disease_name}: {e}")
            combobox['values'] = ["Error fetching"]
            combobox.set("Error fetching")

    def load_selected_disease(self, event):
        selected = self.results_tree.selection()
        if selected:
            disease_id = self.results_tree.item(selected[0], 'values')[0]

            self.status_var.set(f"Loading disease {disease_id}...")
            self.root.update_idletasks()

            disease_data = self.get_kegg_disease(disease_id)
            if disease_data:
                self.display_disease(disease_data)
            else:
                messagebox.showerror("Error", f"Failed to load disease {disease_id}")
                self.status_var.set("Ready")


if __name__ == "__main__":
    root = tk.Tk()
    app = DiseaseGeneApp(root)
    root.mainloop()