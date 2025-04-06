import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QWidget, QComboBox, QPushButton, QHBoxLayout,
                             QLabel, QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from pyvis.network import Network
import pandas as pd
import networkx as nx


class GeneNetworkViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Gene Network Viewer")
        self.setGeometry(100, 100, 1000, 800)

        # Create UI elements
        self.browser = QWebEngineView()
        self.gene_dropdown = QComboBox()
        self.reset_button = QPushButton("Reset View")
        self.central_gene_label = QLabel("Central Gene:")
        self.central_gene_display = QLabel("672")  # Display central gene as label, not editable
        self.refresh_button = QPushButton("Refresh Graph")

        # Store dataset
        self.df = None

        self.init_ui()
        self.load_data()
        self.init_network_graph()


    def init_ui(self):
        """Initialize the user interface components"""
        # Create control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)

        # Configure inputs
        self.gene_dropdown.setPlaceholderText("Select a gene")
        self.gene_dropdown.setMinimumWidth(200)
        self.reset_button.setFixedWidth(100)
        self.refresh_button.setFixedWidth(100)

        # Style the central gene display
        self.central_gene_display.setStyleSheet("font-weight: bold;")

        # Add widgets to control panel
        control_layout.addWidget(self.central_gene_label)
        control_layout.addWidget(self.central_gene_display)
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.gene_dropdown)
        control_layout.addWidget(self.reset_button)
        control_panel.setFixedHeight(50)

        # Main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.browser)

        self.setCentralWidget(central_widget)

        # Connect signals
        self.reset_button.clicked.connect(self.reset_view)
        self.gene_dropdown.currentTextChanged.connect(self.highlight_gene)
        self.refresh_button.clicked.connect(self.refresh_graph)

    def load_data(self):
        """Load and prepare gene data"""
        try:
            self.df = pd.read_csv("top_20_genes_by_pathway.csv")
            self.df['gene_id'] = self.df['gene_id'].astype(str)

            # Populate dropdown
            self.gene_dropdown.clear()
            self.gene_dropdown.addItem("All Genes")
            for _, row in self.df.iterrows():
                self.gene_dropdown.addItem(f"hsa:{row['gene_id']}")

        except Exception as e:
            self.show_error(f"Error loading data: {str(e)}")

    def init_network_graph(self):
        try:
            if self.df is None:
                self.show_error("No data loaded")
                return

            # Get central gene
            central_gene = self.central_gene_display.text()

            # Create network graph
            G = nx.Graph()

            # Add central gene if missing
            if central_gene not in self.df['gene_id'].values:
                print(f"Adding central gene {central_gene}")
                self.df = pd.concat([self.df, pd.DataFrame({
                    'gene_id': [central_gene],
                    'pathway_count': [self.df['pathway_count'].mean()],
                    'similarity_score': [1.0]  # Central gene has perfect similarity to itself
                })], ignore_index=True)

            # Create nodes and edges
            max_similarity = self.df['similarity_score'].max()
            min_similarity = self.df['similarity_score'].min()
            similarity_range = max_similarity - min_similarity

            for _, row in self.df.iterrows():
                gene_id = row['gene_id']
                is_central = gene_id == central_gene

                # Node styling
                node_color = "#E91E63" if is_central else "#4CAF50"
                node_size = 30 if is_central else 15 + (row['pathway_count'] * 2)

                # For central gene, always show similarity as 1.0
                display_similarity = 1.0 if is_central else row['similarity_score']

                G.add_node(
                    gene_id,
                    size=node_size,
                    color=node_color,
                    title=f"Gene: hsa:{gene_id}<br>Pathways: {row['pathway_count']}<br>Similarity: {display_similarity:.3f}",
                    label=f"hsa:{gene_id}"
                )

                # Create edges using similarity score for distance
                if not is_central and central_gene in self.df['gene_id'].values:
                    # Normalize similarity to create more varied distances
                    normalized_similarity = 0.5
                    if similarity_range > 0:
                        normalized_similarity = (row['similarity_score'] - min_similarity) / similarity_range

                    # Higher similarity = shorter distance (closer nodes)
                    distance = 400 - (normalized_similarity * 300)

                    G.add_edge(
                        central_gene,
                        gene_id,
                        title=f"Similarity: {row['similarity_score']:.3f}",
                        color=self.get_edge_color(row['similarity_score']),
                        length=distance,
                        width=1 + normalized_similarity * 3  # Thicker lines for more similar genes
                    )

            # Configure network
            net = Network(height="750px", width="100%", bgcolor="#ffffff")
            net.from_nx(G)

            # Physics configuration for better visualization
            net.set_options("""{
                "nodes": {
                    "shape": "dot",
                    "scaling": {"min": 10, "max": 30},
                    "shadow": true,
                    "font": {"size": 14, "face": "Tahoma"}
                },
                "edges": {
                    "color": {"inherit": false},
                    "smooth": {"type": "continuous"},
                    "shadow": true
                },
                "physics": {
                    "enabled": true,
                    "barnesHut": {
                        "gravitationalConstant": -2000,
                        "centralGravity": 0.1,
                        "springLength": 200,
                        "springConstant": 0.05,
                        "damping": 0.09,
                        "avoidOverlap": 0.5
                    }
                },
                "interaction": {
                    "navigationButtons": true,
                    "keyboard": true,
                    "hover": true,
                    "tooltipDelay": 200
                }
            }""")

            # Use a fixed file for all operations
            fixed_file = "gene_network_display.html"

            # Write the HTML to the file
            net.write_html(fixed_file, open_browser=False)
            self.fix_tooltip_display(fixed_file)

            # Load the file using QUrl.fromLocalFile
            self.browser.load(QUrl.fromLocalFile(os.path.abspath(fixed_file)))

        except Exception as e:
            print(f"Error creating graph: {str(e)}")
            self.show_error(str(e))

    def fix_tooltip_display(self, filename=None):
        """Fix tooltip display issues by modifying the HTML file"""
        try:
            file_to_fix = filename if filename else self.html_file
            with open(file_to_fix, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace vis.js tooltip handling with custom tooltips
            tooltip_js = """
            <style>
            .custom-tooltip {
                position: absolute;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-family: Arial, sans-serif;
                font-size: 12px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                z-index: 1000;
                pointer-events: none;
                max-width: 300px;
            }
            </style>
            <script>
            // Create custom tooltip element
            var tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.style.display = 'none';
            document.body.appendChild(tooltip);

            // Show tooltip on hover
            network.on("hoverNode", function(params) {
                var node = nodes.get(params.node);
                if (node.title) {
                    tooltip.innerHTML = node.title;
                    tooltip.style.display = 'block';

                    // Position tooltip near cursor
                    var pos = network.getPositions([params.node])[params.node];
                    var canvasPos = network.canvasToDOM(pos);
                    tooltip.style.left = (canvasPos.x + 10) + 'px';
                    tooltip.style.top = (canvasPos.y + 10) + 'px';
                }
            });

            network.on("hoverEdge", function(params) {
                var edge = edges.get(params.edge);
                if (edge.title) {
                    tooltip.innerHTML = edge.title;
                    tooltip.style.display = 'block';

                    // Position tooltip near cursor
                    var canvas = network.canvas.frame.canvas;
                    var rect = canvas.getBoundingClientRect();
                    tooltip.style.left = (event.clientX - rect.left + 10) + 'px';
                    tooltip.style.top = (event.clientY - rect.top + 10) + 'px';
                }
            });

            // Hide tooltip when not hovering
            network.on("blurNode", function() {
                tooltip.style.display = 'none';
            });

            network.on("blurEdge", function() {
                tooltip.style.display = 'none';
            });

            // Update tooltip position on drag
            network.on("dragStart", function() {
                tooltip.style.display = 'none';
            });
            </script>
            """

            # Insert our custom tooltip code before </body>
            content = content.replace('</body>', f'{tooltip_js}\n</body>')

            with open(file_to_fix, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"Error fixing tooltip: {str(e)}")

    def get_edge_color(self, similarity):
        """Generate color for edge based on similarity score"""
        # Color gradient from red (low similarity) to green (high similarity)
        if similarity < 0.3:
            return "#FF5252"  # Red
        elif similarity < 0.6:
            return "#FFC107"  # Amber
        else:
            return "#4CAF50"  # Green

    def highlight_gene(self, text):
        """Highlight selected gene in the network"""
        try:
            if text == "All Genes":
                self.reset_view()
                return

            gene_id = text.split(":")[1]
            central_gene = self.central_gene_display.text()

            js = f"""
            // Reset all nodes
            var nodes = network.body.data.nodes;
            nodes.update(
                nodes.get().map(function(n) {{
                    return {{
                        id: n.id,
                        color: n.id === "{central_gene}" ? "#E91E63" : "#4CAF50"
                    }};
                }})
            );

            // Highlight selected
            nodes.update({{
                id: "{gene_id}",
                color: "#FFC107",
                size: 30
            }});

            network.focus("{gene_id}", {{scale: 1.2}});
            """
            self.browser.page().runJavaScript(js)
        except Exception as e:
            print(f"Highlight error: {str(e)}")

    def refresh_graph(self):
        """Refresh the graph with current settings"""
        self.init_network_graph()

    def reset_view(self):
        """Reset view to initial state"""
        self.browser.page().runJavaScript("network.fit()")
        self.gene_dropdown.setCurrentIndex(0)

    def show_error(self, message):
        """Display error message in browser"""
        QMessageBox.critical(self, "Error", message)
        self.browser.setHtml(f"""
            <div style="
                padding: 20px;
                font-family: Arial;
                color: #dc3545;
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                margin: 20px;
            ">
                <h3>Error</h3>
                <p>{message}</p>
            </div>
        """)

    def closeEvent(self, event):
        """Clean up HTML files on close"""
        try:
            if os.path.exists("gene_network_display.html"):
                os.remove("gene_network_display.html")
        except Exception as e:
            print(f"Error removing files: {str(e)}")
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeneNetworkViewer()
    window.show()
    sys.exit(app.exec_())