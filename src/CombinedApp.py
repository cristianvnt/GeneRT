# # In your main application file (modified version)
# from tkinter import ttk
#
#
# class CombinedApp:
#     def __init__(self, root):
#         self.root = root
#         root.title("Bioinformatics Tool")
#         root.geometry("1000x800")
#
#         # Create notebook (tabbed interface)
#         self.notebook = ttk.Notebook(root)
#         self.notebook.pack(fill=tk.BOTH, expand=True)
#
#         # Add gene search tab
#         self.gene_tab = ttk.Frame(self.notebook)
#         self.gene_app = GeneInfoApp(self.gene_tab)  # Your existing gene app
#         self.notebook.add(self.gene_tab, text="Gene Search")
#
#         # Add disease search tab
#         self.disease_tab = ttk.Frame(self.notebook)
#         self.disease_app = DiseaseSearchApp(self.disease_tab)  # The new disease app
#         self.notebook.add(self.disease_tab, text="Disease Search")
#
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = CombinedApp(root)
#     root.mainloop()