import sys
import os
import requests
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QWidget, QComboBox, QPushButton, QHBoxLayout,
                             QLabel, QMessageBox, QTableWidget, QTableWidgetItem,
                             QSplitter, QFrame, QHeaderView)
from PyQt5.QtCore import QUrl, Qt, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWebChannel import QWebChannel
from pyvis.network import Network
import pandas as pd
import networkx as nx


class GeneDrugTargetFinder:
    def __init__(self, gene_symbol="EGFR"):
        self.gene_symbol = gene_symbol

    def find_info(self):
        """Find disease associations and drug targets for a gene"""
        try:
            # Get KEGG data
            kegg_gene_id = self.gene_symbol
            if not kegg_gene_id.startswith("hsa:"):
                kegg_gene_id = f"hsa:{self.gene_symbol}"

            kegg_gene_data = self.get_kegg_gene_info(kegg_gene_id)

            # Extract diseases
            diseases = self.extract_diseases(kegg_gene_data)

            # Extract drug targets
            drug_targets = self.extract_drug_targets(kegg_gene_data)

            return diseases, drug_targets

        except Exception as e:
            print(f"Error finding gene info: {str(e)}")
            return [], []

    def get_kegg_gene_info(self, kegg_id):
        """Request raw data from KEGG"""
        kegg_url = f"http://rest.kegg.jp/get/{kegg_id}"
        response = requests.get(kegg_url)
        response.raise_for_status()
        return self.parse_kegg_response(response.text)

    def parse_kegg_response(self, text):
        """Parse flat KEGG file into a dictionary"""
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
        """Extract diseases from the DISEASE section"""
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
        """Extract drugs from the DRUG_TARGET section"""
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


# Bridge class for direct communication between JavaScript and Python
class Bridge(QObject):
    # Signal to notify that a node was clicked
    nodeClicked = pyqtSignal(str, str)

    @pyqtSlot(str, str)
    def onNodeClick(self, node_id, node_label):
        # Emit the signal with the node information
        print(f"Bridge: Node clicked - {node_id}, {node_label}")
        self.nodeClicked.emit(node_id, node_label)


# Custom web page to intercept console messages
class CustomWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        print(f"JS Console: {message} (Line {line})")


class GeneNetworkViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Gene Network Viewer")
        self.setGeometry(100, 100, 1000, 800)
        self.gene_id = None

        # Create UI elements
        self.browser = QWebEngineView()
        self.page = CustomWebPage(self.browser)
        self.browser.setPage(self.page)

        self.gene_dropdown = QComboBox()
        self.reset_button = QPushButton("Reset View")
        self.central_gene_label = QLabel("Central Gene:")
        self.central_gene_display = QLabel("672")  # Display central gene as label, not editable
        self.refresh_button = QPushButton("Refresh Graph")

        # Create info panel for drugs and diseases
        self.info_panel = QWidget()
        self.info_panel_layout = QVBoxLayout(self.info_panel)
        self.gene_info_label = QLabel("Gene Information")
        self.gene_info_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Create tables for drugs and diseases
        self.drug_table = QTableWidget()
        self.drug_table.setColumnCount(2)
        self.drug_table.setHorizontalHeaderLabels(["Drug Name", "Drug IDs"])

        self.disease_table = QTableWidget()
        self.disease_table.setColumnCount(2)
        self.disease_table.setHorizontalHeaderLabels(["Disease ID", "Disease Name"])

        # Add components to info panel
        self.info_panel_layout.addWidget(self.gene_info_label)

        # Status label for API requests
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        self.info_panel_layout.addWidget(self.status_label)

        # Add section labels
        self.drug_label = QLabel("Related Drugs")
        self.drug_label.setStyleSheet("font-weight: bold;")
        self.info_panel_layout.addWidget(self.drug_label)
        self.info_panel_layout.addWidget(self.drug_table)

        self.disease_label = QLabel("Associated Diseases")
        self.disease_label.setStyleSheet("font-weight: bold;")
        self.info_panel_layout.addWidget(self.disease_label)
        self.info_panel_layout.addWidget(self.disease_table)

        # Initially hide the info panel
        self.info_panel.setVisible(False)
        self.info_panel.setMaximumWidth(400)

        # Store dataset
        self.df = None

        # Create GeneDrugTargetFinder instance
        self.finder = GeneDrugTargetFinder(self.gene_id)

        # Set up web channel for JS-Python communication
        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("pybridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # Connect the bridge's nodeClicked signal to our slot
        self.bridge.nodeClicked.connect(self.on_node_clicked)

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

        # Create a splitter for main content and info panel
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.browser)
        self.splitter.addWidget(self.info_panel)
        self.splitter.setSizes([700, 300])

        # Main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.splitter)

        self.setCentralWidget(central_widget)

        # Connect signals
        self.reset_button.clicked.connect(self.reset_view)
        self.gene_dropdown.currentTextChanged.connect(self.highlight_gene)
        self.refresh_button.clicked.connect(self.refresh_graph)

        # Set up table properties
        for table in [self.drug_table, self.disease_table]:
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

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

            central_gene = self.central_gene_display.text()

            # Dacă gene_id-ul central lipsește, îl adăugăm
            if central_gene not in self.df['gene_id'].values:
                print(f"Adding central gene {central_gene}")
                self.df = pd.concat([self.df, pd.DataFrame({
                    'gene_id': [central_gene],
                    'total_score': [self.df['total_score'].mean()],
                    'similarity_score': [1.0]
                })], ignore_index=True)

            # Precalcul pentru normalizare
            max_similarity = self.df['similarity_score'].max()
            min_similarity = self.df['similarity_score'].min()
            similarity_range = max_similarity - min_similarity

            G = nx.Graph()

            for _, row in self.df.iterrows():
                gene_id = row['gene_id']
                is_central = gene_id == central_gene

                node_size = 30 if is_central else 10 + (row['total_score'] * 20)
                node_color = "#E91E63" if is_central else "#4CAF50"
                display_similarity = 1.0 if is_central else row['similarity_score']

                G.add_node(
                    gene_id,
                    size=node_size,
                    color=node_color,
                    title=f"Gene: hsa:{gene_id}<br>Total Score: {row['total_score']:.3f}<br>Similarity: {display_similarity:.3f}",
                    label=f"hsa:{gene_id}"
                )

                if not is_central:
                    normalized_similarity = 0.5
                    if similarity_range > 0:
                        normalized_similarity = (row['similarity_score'] - min_similarity) / similarity_range

                    distance = 400 - (normalized_similarity * 300)

                    G.add_edge(
                        central_gene,
                        gene_id,
                        title=f"Similarity: {row['similarity_score']:.3f}",
                        color=self.get_edge_color(row['similarity_score']),
                        length=distance,
                        width=1 + normalized_similarity * 3
                    )

            net = Network(height="750px", width="100%", bgcolor="#ffffff")
            net.from_nx(G)

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

            fixed_file = "gene_network_display.html"
            net.write_html(fixed_file, open_browser=False)
            self.fix_tooltip_display(fixed_file)
            self.add_node_click_handler(fixed_file)
            self.browser.load(QUrl.fromLocalFile(os.path.abspath(fixed_file)))

        except Exception as e:
            print(f"Error creating graph: {str(e)}")
            self.show_error(str(e))

    def fix_tooltip_display(self, filename=None):
        """Fix tooltip display issues by modifying the HTML file"""
        try:
            file_to_fix = filename
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

    def add_node_click_handler(self, filename):
        """Add click event handler for nodes to show drug/disease info - IMPROVED VERSION"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add web channel support for direct communication between JS and Python
            web_channel_js = """
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
            // Global variable to store the Python bridge
            var pybridge;

            // Initialize the web channel
            document.addEventListener("DOMContentLoaded", function() {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    // Get the Python bridge object
                    pybridge = channel.objects.pybridge;
                    console.log("Web channel initialized");
                });
            });

            // Add click handler for nodes
            network.on("click", function(params) {
                if (params.nodes.length > 0) {
                    var nodeId = params.nodes[0];
                    var nodeObj = nodes.get(nodeId);
                    var nodeLabel = nodeObj.label || nodeId;

                    console.log("Node clicked:", nodeId, nodeLabel);

                    // Use the Python bridge to send the click event
                    if (pybridge) {
                        pybridge.onNodeClick(nodeId, nodeLabel);
                    } else {
                        console.error("Python bridge not available");

                        // Fallback to postMessage if bridge not available
                        window.parent.postMessage(JSON.stringify({
                            action: "nodeClick",
                            nodeId: nodeId,
                            nodeLabel: nodeLabel
                        }), "*");
                    }
                }
            });
            </script>
            """

            # Insert web channel code before </body>
            content = content.replace('</body>', f'{web_channel_js}\n</body>')

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"Error adding node click handler: {str(e)}")

    def on_node_clicked(self, node_id, node_label):
        """Handle node click event from the bridge"""
        print(f"Node clicked: {node_id}, {node_label}")

        # Extract gene ID from label if needed
        gene_id = node_id
        if node_label and ":" in node_label:
            gene_id = node_label.split(":")[1]

        # Highlight the clicked node and reduce opacity of others
        js = f"""
        // Reduce opacity for all nodes and edges
        var nodes = network.body.data.nodes;
        var edges = network.body.data.edges;

        // Update all nodes with reduced opacity
        nodes.update(
            nodes.get().map(function(n) {{
                return {{
                    id: n.id,
                    opacity: 0.3,
                    color: {{
                        opacity: 0.3
                    }}
                }};
            }})
        );

        // Update all edges with reduced opacity
        edges.update(
            edges.get().map(function(e) {{
                return {{
                    id: e.id,
                    color: {{
                        opacity: 0.2
                    }}
                }};
            }})
        );

        // Highlight the selected node with full opacity and bright color
        nodes.update({{
            id: "{node_id}",
            opacity: 1.0,
            color: {{
                background: "#FFC107",
                border: "#FF9800",
                opacity: 1.0
            }},
            size: 35,
            borderWidth: 3
        }});

        // Highlight direct connections to this node
        var connectedEdges = network.getConnectedEdges("{node_id}");
        var connectedNodes = [];

        // Get nodes connected to this node
        connectedEdges.forEach(function(edgeId) {{
            var edge = edges.get(edgeId);
            if (edge.from === "{node_id}") {{
                connectedNodes.push(edge.to);
            }} else {{
                connectedNodes.push(edge.from);
            }}

            // Highlight the edge
            edges.update({{
                id: edgeId,
                color: {{
                    opacity: 0.9
                }},
                width: 2
            }});
        }});

        // Highlight connected nodes
        connectedNodes.forEach(function(connectedId) {{
            nodes.update({{
                id: connectedId,
                opacity: 0.7,
                color: {{
                    opacity: 0.7
                }}
            }});
        }});

        // Focus on the node with slight zoom
        network.focus("{node_id}", {{
            scale: 1.2,
            animation: {{
                duration: 300,
                easingFunction: "easeInOutQuad"
            }}
        }});
        """
        self.browser.page().runJavaScript(js)

        # Display gene info in the panel
        self.display_gene_info(gene_id)

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
            // Reduce opacity for all nodes and edges
            var nodes = network.body.data.nodes;
            var edges = network.body.data.edges;

            // Update all nodes with reduced opacity
            nodes.update(
                nodes.get().map(function(n) {{
                    return {{
                        id: n.id,
                        opacity: 0.3,
                        color: {{
                            background: n.id === "{central_gene}" ? "#E91E63" : "#4CAF50",
                            opacity: 0.3
                        }}
                    }};
                }})
            );

            // Update all edges with reduced opacity
            edges.update(
                edges.get().map(function(e) {{
                    return {{
                        id: e.id,
                        color: {{
                            opacity: 0.2
                        }}
                    }};
                }})
            );

            // Highlight the selected node with full opacity and bright color
            nodes.update({{
                id: "{gene_id}",
                opacity: 1.0,
                color: {{
                    background: "#FFC107",
                    border: "#FF9800",
                    opacity: 1.0
                }},
                size: 35,
                borderWidth: 3
            }});

            // Highlight direct connections to this node
            var connectedEdges = network.getConnectedEdges("{gene_id}");
            var connectedNodes = [];

            // Get nodes connected to this node
            connectedEdges.forEach(function(edgeId) {{
                var edge = edges.get(edgeId);
                if (edge.from === "{gene_id}") {{
                    connectedNodes.push(edge.to);
                }} else {{
                    connectedNodes.push(edge.from);
                }}

                // Highlight the edge
                edges.update({{
                    id: edgeId,
                    color: {{
                        opacity: 0.9
                    }},
                    width: 2
                }});
            }});

            // Highlight connected nodes
            connectedNodes.forEach(function(connectedId) {{
                nodes.update({{
                    id: connectedId,
                    opacity: 0.7,
                    color: {{
                        opacity: 0.7
                    }}
                }});
            }});

            network.focus("{gene_id}", {{
                scale: 1.2,
                animation: {{
                    duration: 300,
                    easingFunction: "easeInOutQuad"
                }}
            }});
            """
            self.browser.page().runJavaScript(js)

            # Also display the gene info
            self.display_gene_info(gene_id)

        except Exception as e:
            print(f"Highlight error: {str(e)}")


    def display_gene_info(self, gene_id):
        """Display drug and disease information for the selected gene from KEGG"""
        try:
            # Print debug info
            print(f"Displaying gene info for: {gene_id}")

            # Show the info panel if it's hidden
            self.info_panel.setVisible(True)

            # Update gene info label
            self.gene_info_label.setText(f"Gene Information: hsa:{gene_id}")

            # Update status
            self.status_label.setText("Fetching data from KEGG...")
            self.status_label.setStyleSheet("color: blue; font-style: italic;")
            QApplication.processEvents()  # Update UI

            # Clear previous data
            self.drug_table.setRowCount(0)
            self.disease_table.setRowCount(0)

            # Set gene for finder
            self.finder.gene_symbol = gene_id

            # Get related diseases and drugs
            diseases, drug_targets = self.finder.find_info()

            # Update status
            self.status_label.setText(f"Data retrieved for hsa:{gene_id}")
            self.status_label.setStyleSheet("color: green; font-style: italic;")

            # Populate drug table
            if drug_targets:
                self.drug_table.setRowCount(len(drug_targets))
                for i, (drug_name, drug_ids) in enumerate(drug_targets):
                    self.drug_table.setItem(i, 0, QTableWidgetItem(drug_name))
                    self.drug_table.setItem(i, 1, QTableWidgetItem(" ".join(drug_ids)))
            else:
                self.drug_table.setRowCount(1)
                self.drug_table.setSpan(0, 0, 1, 2)
                self.drug_table.setItem(0, 0, QTableWidgetItem("No drug data available for this gene"))

            # Populate disease table
            if diseases:
                self.disease_table.setRowCount(len(diseases))
                for i, (disease_id, disease_name) in enumerate(diseases):
                    self.disease_table.setItem(i, 0, QTableWidgetItem(disease_id))
                    self.disease_table.setItem(i, 1, QTableWidgetItem(disease_name))
            else:
                self.disease_table.setRowCount(1)
                self.disease_table.setSpan(0, 0, 1, 2)
                self.disease_table.setItem(0, 0, QTableWidgetItem("No disease data available for this gene"))

            # Resize columns to fit content
            self.drug_table.resizeColumnsToContents()
            self.disease_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error displaying gene info: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red; font-style: italic;")

    def refresh_graph(self):
        """Refresh the graph with current settings"""
        self.init_network_graph()

    def reset_view(self):
        """Reset view to initial state"""
        js = """
        // Reset all nodes and edges to full opacity
        var nodes = network.body.data.nodes;
        var edges = network.body.data.edges;

        // Get central gene
        var centralId = "672";  // Assuming this is your central gene ID

        // Reset all nodes
        nodes.update(
            nodes.get().map(function(n) {
                return {
                    id: n.id,
                    opacity: 1.0,
                    color: {
                        background: n.id === centralId ? "#E91E63" : "#4CAF50",
                        opacity: 1.0
                    },
                    size: n.id === centralId ? 30 : 15,
                    borderWidth: 1
                };
            })
        );

        // Reset all edges
        edges.update(
            edges.get().map(function(e) {
                return {
                    id: e.id,
                    color: {
                        opacity: 1.0
                    },
                    width: 1
                };
            })
        );

        network.fit({
            animation: {
                duration: 500,
                easingFunction: "easeInOutQuad"
            }
        });
        """
        self.browser.page().runJavaScript(js)
        self.gene_dropdown.setCurrentIndex(0)

        # Hide the info panel
        self.info_panel.setVisible(False)

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