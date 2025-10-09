#!/usr/bin/env python3

import sys
import re
from pathlib import Path
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPlainTextEdit, QPushButton, QFileDialog, QMessageBox,
    QLineEdit, QCheckBox, QFrame, QSpacerItem, QSizePolicy
)

# ---------- Config ----------
DEFAULT_TEMPLATE = "https://calendar.google.com/calendar/u/0/htmlembed?src=XYZ"
WINDOW_TITLE = "⚡ Calendar Link Generator"
FONT_MONO = "Consolas, Monaco, 'Courier New', monospace"

# ---------- Helper functions ----------
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def clean_and_split_emails(text: str):
    parts = re.split(r'[\n,;\s]+', text.strip())
    seen = set()
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


def generate_link(template: str, email: str) -> str:
    if "XYZ" in template:
        return template.replace("XYZ", email)
    if "{email}" in template:
        return template.replace("{email}", email)
    # fallback: append as src param if present, otherwise append
    if "src=" in template and template.endswith("="):
        return template + email
    return template + email

# ---------- UI ----------
class HackerVibeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(900, 650)
        self.setWindowIcon(QIcon())

        # Central widget
        w = QWidget()
        w.setObjectName("main_widget")
        self.setCentralWidget(w)
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # Header (big hacker vibe label)
        header = QLabel("<span style='font-size:20pt; font-weight:700'>Google</span> <span style='color:#7CFC00'>— Calendar Link Generator</span>")
        header.setTextFormat(Qt.RichText)
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(header)

        # Top controls: template, validation, load/save buttons
        top_row = QHBoxLayout()
        layout.addLayout(top_row)

        self.template_input = QLineEdit(DEFAULT_TEMPLATE)
        self.template_input.setPlaceholderText("URL template (use XYZ or {email})")
        self.template_input.setToolTip("Template where 'XYZ' or '{email}' will be replaced with each email")
        top_row.addWidget(self.template_input, stretch=6)

        self.validate_cb = QCheckBox("Validate emails")
        self.validate_cb.setChecked(True)
        top_row.addWidget(self.validate_cb, stretch=0)

        self.load_btn = QPushButton("Load .txt")
        self.load_btn.clicked.connect(self.load_file)
        top_row.addWidget(self.load_btn, stretch=0)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(self.generate)
        top_row.addWidget(self.generate_btn, stretch=0)

        # Middle: two panels side-by-side (emails input | links output)
        mid_row = QHBoxLayout()
        layout.addLayout(mid_row, stretch=1)

        # Left panel
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(6, 6, 6, 6)

        left_layout.addWidget(QLabel("Paste or edit emails (one per line or separated by commas/spaces):"))
        self.email_editor = QPlainTextEdit()
        self.email_editor.setPlaceholderText("john@example.com\nanna@site.com, someone@org.com")
        self.email_editor.setFont(QFont(FONT_MONO, 10))
        left_layout.addWidget(self.email_editor, stretch=1)

        left_buttons = QHBoxLayout()
        self.copy_emails_btn = QPushButton("Copy Emails")
        self.copy_emails_btn.clicked.connect(self.copy_emails)
        left_buttons.addWidget(self.copy_emails_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(lambda: self.email_editor.clear())
        left_buttons.addWidget(self.clear_btn)

        left_buttons.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        left_layout.addLayout(left_buttons)

        mid_row.addWidget(left_frame, stretch=5)

        # Right panel
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(6, 6, 6, 6)

        right_layout.addWidget(QLabel("Generated links (preview):"))
        self.link_output = QPlainTextEdit()
        self.link_output.setReadOnly(False)
        self.link_output.setFont(QFont(FONT_MONO, 10))
        right_layout.addWidget(self.link_output, stretch=1)

        right_buttons = QHBoxLayout()
        self.copy_links_btn = QPushButton("Copy Links")
        self.copy_links_btn.clicked.connect(self.copy_links)
        right_buttons.addWidget(self.copy_links_btn)

        self.save_links_btn = QPushButton("Save Links")
        self.save_links_btn.clicked.connect(self.save_links)
        right_buttons.addWidget(self.save_links_btn)

        self.clear_links_btn = QPushButton("Clear Links")
        self.clear_links_btn.clicked.connect(lambda: self.link_output.clear())
        right_buttons.addWidget(self.clear_links_btn)

        right_buttons.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        right_layout.addLayout(right_buttons)

        mid_row.addWidget(right_frame, stretch=6)

        # Footer: stats and small actions
        footer = QHBoxLayout()
        layout.addLayout(footer)

        self.status_label = QLabel("Ready — paste emails and hit Generate")
        footer.addWidget(self.status_label)

        footer.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        footer.addWidget(self.export_csv_btn)

        # Small keyboard shortcuts
        self.generate_btn.setShortcut("Ctrl+G")
        self.copy_links_btn.setShortcut("Ctrl+L")

        # Apply dark hacker style
        self.apply_style()

    # ---------- Actions ----------
    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Email List", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                txt = Path(path).read_text(encoding='utf-8', errors='ignore')
                self.email_editor.setPlainText(txt)
                self.status(f"Loaded {Path(path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read file:\n{e}")

    def generate(self):
        raw = self.email_editor.toPlainText()
        emails = clean_and_split_emails(raw)
        if not emails:
            QMessageBox.warning(self, "No emails", "Please paste or load some emails first.")
            return

        valid_only = self.validate_cb.isChecked()
        template = self.template_input.text().strip() or DEFAULT_TEMPLATE

        links = []
        invalid = []
        for e in emails:
            if valid_only and not is_valid_email(e):
                invalid.append(e)
                continue
            links.append(generate_link(template, e))

        if invalid:
            self.status(f"Generated {len(links)} links — skipped {len(invalid)} invalid emails")
            # show a subtle popover for invalids
            msg = f"Skipped {len(invalid)} invalid emails (first 5 shown below):\n" + "\n".join(invalid[:5])
            QMessageBox.information(self, "Invalid emails", msg)
        else:
            self.status(f"Generated {len(links)} links")

        self.link_output.setPlainText('\n'.join(links))

    def save_links(self):
        if not self.link_output.toPlainText().strip():
            QMessageBox.warning(self, "No links", "No links to save. Generate first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Links", "links.txt", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                Path(path).write_text(self.link_output.toPlainText(), encoding='utf-8')
                self.status(f"Saved links -> {Path(path).name}")
                QMessageBox.information(self, "Saved", f"Links saved to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def save_links_quiet(self, path: Path):
        Path(path).write_text(self.link_output.toPlainText(), encoding='utf-8')

    def export_csv(self):
        if not self.link_output.toPlainText().strip():
            QMessageBox.warning(self, "No links", "Generate links before exporting CSV.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "links.csv", "CSV Files (*.csv);;All Files (*)")
        if path:
            try:
                emails = clean_and_split_emails(self.email_editor.toPlainText())
                links = [l.strip() for l in self.link_output.toPlainText().splitlines() if l.strip()]
                # pairwise -- if counts mismatch, export what we have
                rows = [f'"{emails[i]}","{links[i]}"' for i in range(min(len(emails), len(links)))]
                Path(path).write_text('\n'.join(rows) + '\n', encoding='utf-8')
                QMessageBox.information(self, "CSV Exported", f"CSV exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export CSV:\n{e}")

    def copy_links(self):
        txt = self.link_output.toPlainText()
        if not txt.strip():
            QMessageBox.warning(self, "No links", "Nothing to copy. Generate first.")
            return
        QApplication.clipboard().setText(txt)
        self.status("Links copied to clipboard")

    def copy_emails(self):
        txt = self.email_editor.toPlainText()
        if not txt.strip():
            QMessageBox.warning(self, "No emails", "Nothing to copy.")
            return
        QApplication.clipboard().setText(txt)
        self.status("Emails copied to clipboard")

    def status(self, text: str):
        self.status_label.setText(text)
        # auto-clear after 6 seconds
        QTimer.singleShot(6000, lambda: self.status_label.setText("Ready"))

    def apply_style(self):
        # Dark, matrix-y styling
        qss = r'''
        QWidget#main_widget { background: #0b0f0b; color: #C7F9C7; }
        QLabel { color: #9ef07a; }
        QLineEdit, QPlainTextEdit, QTextEdit { background: #091109; color: #C7F9C7; border: 1px solid #173617; }
        QPushButton { background: #0f3b0f; color: #d9ffd9; border-radius: 6px; padding:6px; }
        QPushButton:hover { background: #1a5a1a; }
        QCheckBox { color: #9ef07a; }
        QScrollBar:vertical { background: #071007; width:10px; }
        QScrollBar::handle:vertical { background: #164816; border-radius:5px; }
        '''
        self.setStyleSheet(qss)

# ---------- Entrypoint ----------
def main():
    app = QApplication(sys.argv)
    font = QFont()
    font.setFamily(FONT_MONO)
    font.setPointSize(10)
    app.setFont(font)

    win = HackerVibeWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
