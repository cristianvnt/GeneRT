import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QTextEdit,
    QVBoxLayout, QWidget
)
from api import openTargetsDrugEvidence


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PHv17: Gene Explorer - Drug Repurposer App")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Add welcome label
        self.label = QLabel("Welcome to PHv17!")
        self.layout.addWidget(self.label)

        # Add a button to fetch drug evidence
        self.fetch_button = QPushButton("Fetch Drug Evidence")
        self.fetch_button.clicked.connect(self.fetch_drug_evidence)
        self.layout.addWidget(self.fetch_button)

        # Add a text area to display results
        self.text_area = QTextEdit()
        self.layout.addWidget(self.text_area)

    def fetch_drug_evidence(self):
        try:
            response_json = openTargetsDrugEvidence.query_open_targets_api()
            data = openTargetsDrugEvidence.parse_drug_evidence(response_json)
            display_text = self.format_drug_evidence(data)
            self.text_area.setPlainText(display_text)
        except Exception as e:
            self.text_area.setPlainText(f"Error: {e}")

    def format_drug_evidence(self, data):
        lines = []
        lines.append("=== OpenTargets Drug Evidence ===")
        lines.append(f"Target Gene: TP53 ({data['target_gene']})")
        lines.append(f"Total Associations Found: {data['count']}")
        lines.append("================================")
        lines.append("")
        for item in data["rows"]:
            lines.append(f"Drug:    {item['drug_name']}")
            lines.append(f"ID:      {item['drug_id']}")
            lines.append(f"Disease: {item['disease_name']}")
            lines.append(f"ID:      {item['disease_id']}")
            lines.append("--------------------------------")
        return "\n".join(lines)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
