import sys
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTextEdit, QLabel,
    QMessageBox, QStatusBar
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

class EmailExtractorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Email Extractor – Security Recon Tool")
        self.setGeometry(300, 150, 900, 650)

        self.emails = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Email Extractor")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Professional Recon & Bug Bounty Utility")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        btn_layout = QHBoxLayout()

        self.open_btn = QPushButton("📂 Open TXT File")
        self.open_btn.setFixedHeight(40)
        self.open_btn.clicked.connect(self.open_file)

        self.save_btn = QPushButton("💾 Save Emails")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self.save_file)

        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        self.text_area = QTextEdit()
        self.text_area.setFont(QFont("Consolas", 11))
        self.text_area.setPlaceholderText("Extracted emails will appear here...")
        self.text_area.setReadOnly(True)

        layout.addWidget(self.text_area)

        self.status = QStatusBar()
        self.status.showMessage("Ready")

        layout.addWidget(self.status)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #EAEAEA;
            }
            QPushButton {
                background-color: #1f6feb;
                border: none;
                color: white;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #388bfd;
            }
            QTextEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
        """)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select TXT File", "", "Text Files (*.txt);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self.emails = sorted(set(re.findall(EMAIL_REGEX, content)))

        self.text_area.clear()
        self.text_area.setPlainText("\n".join(self.emails))

        self.status.showMessage(f"✅ {len(self.emails)} unique emails extracted")

    def save_file(self):
        if not self.emails:
            QMessageBox.warning(self, "Warning", "No emails to save")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Email List", "emails.txt", "Text Files (*.txt)"
        )

        if not save_path:
            return

        try:
            with open(save_path, "w") as f:
                f.write("\n".join(self.emails))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        QMessageBox.information(self, "Success", "Emails saved successfully")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmailExtractorApp()
    window.show()
    sys.exit(app.exec_())
