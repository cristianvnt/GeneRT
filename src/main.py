import tkinter as tk
from src.geneInfoFetching.GeneInfoFetcher import GeneInfoApp
from src.clasa import DiseaseGeneApp1
from src.disease_search.SimilarDiseases import DiseaseGeneApp


def main():
    root = tk.Tk()
    root.title("Interfață cu taburi rotunjite")
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
    root.configure(bg="#f0f0f0")

    # Culori
    ACTIVE_BG = "white"
    INACTIVE_BG = "#d0d0d0"
    HOVER_BG = "#e0e0e0"
    MAIN_BG = "#f0f0f0"

    # Layout root
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Tab frame (sus)
    tab_frame = tk.Frame(root, bg=MAIN_BG)
    tab_frame.grid(row=0, column=0, sticky="ew")

    # Content frame (jos)
    content_frame = tk.Frame(root, bg=ACTIVE_BG)
    content_frame.grid(row=1, column=0, sticky="nsew")
    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_columnconfigure(0, weight=1)

    # Tab dimensions
    tab_width = int(root.winfo_screenwidth() / 2) - 20
    tab_height = 50
    radius = 20

    canvas1 = tk.Canvas(tab_frame, width=tab_width, height=tab_height, highlightthickness=0, bg=MAIN_BG)
    canvas2 = tk.Canvas(tab_frame, width=tab_width, height=tab_height, highlightthickness=0, bg=MAIN_BG)

    canvas1.pack(side="left", padx=(10, 5), pady=(10, 0))
    canvas2.pack(side="left", padx=(5, 10), pady=(10, 0))

    state = {"active": 1, "hover": 0}
    sections = {}  # Store section frames

    def draw_tab(canvas, text, active, hovered):
        canvas.delete("all")
        bg_color = ACTIVE_BG if active else (HOVER_BG if hovered else INACTIVE_BG)
        text_color = "black"
        w, h, r = tab_width, tab_height, radius

        canvas.create_polygon(
            r, 0, w - r, 0, w, r, w, h, 0, h, 0, r,
            fill=bg_color, outline=bg_color
        )
        canvas.create_oval(0, 0, 2 * r, 2 * r, fill=bg_color, outline=bg_color)
        canvas.create_oval(w - 2 * r, 0, w, 2 * r, fill=bg_color, outline=bg_color)

        canvas.create_text(w // 2, h // 2, text=text, fill=text_color, font=("Arial", 12, "bold"))

    def redraw_tabs(active=None, hover=None):
        if active is not None:
            state["active"] = active
        if hover is not None:
            state["hover"] = hover

        draw_tab(canvas1, "Search for genes...", state["active"] == 1, state["hover"] == 1)
        draw_tab(canvas2, "Search for diseases...", state["active"] == 2, state["hover"] == 2)

    def fade_in_text(label, step=0):
        if step > 10:
            return
        value = 240 - step * 24
        value = max(0, value)
        hex_color = f"#{value:02x}{value:02x}{value:02x}"
        label.config(fg=hex_color)
        label.after(40, lambda: fade_in_text(label, step + 1))

    def switch_to(section_name):
        for name, frame in sections.items():
            if name == section_name:
                frame.grid()
            else:
                frame.grid_remove()

    def show_section1(event=None):
        state["active"] = 1
        redraw_tabs(active=1)

        if "section1" not in sections:
            section1_frame = tk.Frame(content_frame, bg=ACTIVE_BG)
            section1_frame.grid(row=0, column=0, sticky="nsew")
            section1_frame.grid_rowconfigure(0, weight=1)
            section1_frame.grid_columnconfigure(0, weight=1)
            section1_frame.grid_columnconfigure(1, weight=1)

            gene_frame = tk.Frame(section1_frame, bg=ACTIVE_BG)
            gene_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

            right_placeholder = tk.Frame(section1_frame, bg=MAIN_BG)
            right_placeholder.grid(row=0, column=1, sticky="nsew")

            GeneInfoApp(gene_frame)

            sections["section1"] = section1_frame

        switch_to("section1")

    def show_section2(event=None):
        state["active"] = 2
        redraw_tabs(active=2)

        if "section2" not in sections:
            section2_frame = tk.Frame(content_frame, bg=ACTIVE_BG)
            section2_frame.grid(row=0, column=0, sticky="nsew")
            section2_frame.grid_rowconfigure(0, weight=1)
            section2_frame.grid_columnconfigure(0, weight=3)
            section2_frame.grid_columnconfigure(1, weight=7)

            # Partea stângă: ClasaComponent
            left_frame = tk.Frame(section2_frame, bg=ACTIVE_BG)
            left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

            # Partea dreaptă: SimilarDiseasesComponent
            right_frame = tk.Frame(section2_frame, bg=ACTIVE_BG)
            right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

            # Inițializează componentele în cele două frame-uri
            DiseaseGeneApp1(left_frame)
            DiseaseGeneApp(right_frame)

            sections["section2"] = section2_frame

        switch_to("section2")

    # Hover efecte
    canvas1.bind("<Enter>", lambda e: redraw_tabs(hover=1))
    canvas1.bind("<Leave>", lambda e: redraw_tabs(hover=0))
    canvas2.bind("<Enter>", lambda e: redraw_tabs(hover=2))
    canvas2.bind("<Leave>", lambda e: redraw_tabs(hover=0))

    # Click tab
    canvas1.bind("<Button-1>", show_section1)
    canvas2.bind("<Button-1>", show_section2)

    # Inițializare
    show_section1()
    root.mainloop()

if __name__ == "__main__":
    main()
