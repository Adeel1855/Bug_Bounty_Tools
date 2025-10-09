#!/usr/bin/env python3
import sys
import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from functools import partial

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QSpinBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# -------------------- Worker Thread --------------------
class ScannerThread(QThread):
    progress = pyqtSignal(int)
    found = pyqtSignal(str, int)
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, words, url_template, workers=20, timeout=8, verify_ssl=True):
        super().__init__()
        self.words = words
        self.url_template = url_template
        self.workers = workers
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        total = len(self.words)
        if total == 0:
            self.log.emit('No words to test.')
            self.finished.emit()
            return

        self.log.emit(f'Starting scan: {total} words with {self.workers} workers')
        checked = 0

        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futures = {ex.submit(self._fetch, self.url_template.replace('ORG_NAME', w), w): w for w in self.words}
            for fut in as_completed(futures):
                if self._stop:
                    break
                word = futures[fut]
                url = self.url_template.replace('ORG_NAME', word)
                try:
                    code = fut.result()
                    checked += 1
                    self.progress.emit(int(checked / total * 100))
                    if code == 200:
                        self.found.emit(url, code)
                        self.log.emit(f'[FOUND 200] {url}')
                    else:
                        self.log.emit(f'[{code}] {url}')
                except Exception as e:
                    checked += 1
                    self.progress.emit(int(checked / total * 100))
                    self.log.emit(f'[ERROR] {url} -> {e}')
        self.log.emit('Scan finished')
        self.finished.emit()

    def _fetch(self, url, word):
        r = requests.get(url, timeout=self.timeout, verify=self.verify_ssl, allow_redirects=True)
        return r.status_code

# -------------------- Main Window --------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Atlassian ORG_NAME Checker')
        self.setMinimumSize(950, 700)
        self._scanner = None
        self._results = []
        self._setup_ui()
        self._apply_professional_theme()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # URL template input
        tpl_label = QLabel('URL Template (use ORG_NAME placeholder)')
        self.tpl_input = QLineEdit('https://ORG_NAME.atlassian.net/secure/ManageFilters.jspa')
        layout.addWidget(tpl_label)
        layout.addWidget(self.tpl_input)

        # Wordlist inputs
        wl_layout = QHBoxLayout()
        self.load_btn = QPushButton('Load Wordlist')
        self.load_btn.clicked.connect(self.load_wordlist)
        self.clear_btn = QPushButton('Clear Words')
        self.clear_btn.clicked.connect(lambda: self.manual_text.clear())
        wl_layout.addWidget(self.load_btn)
        wl_layout.addWidget(self.clear_btn)
        layout.addLayout(wl_layout)

        manual_label = QLabel('Manual Words (one per line)')
        self.manual_text = QTextEdit()
        self.manual_text.setPlaceholderText('example\ncompany\nmyorg')
        layout.addWidget(manual_label)
        layout.addWidget(self.manual_text)

        # Controls layout
        controls_layout = QHBoxLayout()
        self.workers_spin = QSpinBox(); self.workers_spin.setRange(1, 200); self.workers_spin.setValue(30)
        self.timeout_spin = QSpinBox(); self.timeout_spin.setRange(1, 60); self.timeout_spin.setValue(8)
        self.verify_ssl_cb = QCheckBox('Verify SSL'); self.verify_ssl_cb.setChecked(True)
        self.start_btn = QPushButton('Start Scan'); self.start_btn.clicked.connect(self.start_scan)
        self.stop_btn = QPushButton('Stop'); self.stop_btn.clicked.connect(self.stop_scan); self.stop_btn.setEnabled(False)
        controls_layout.addWidget(QLabel('Workers:')); controls_layout.addWidget(self.workers_spin)
        controls_layout.addWidget(QLabel('Timeout:')); controls_layout.addWidget(self.timeout_spin)
        controls_layout.addWidget(self.verify_ssl_cb)
        controls_layout.addWidget(self.start_btn); controls_layout.addWidget(self.stop_btn)
        layout.addLayout(controls_layout)

        # Progress bar
        self.progress = QProgressBar(); self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Results table
        self.table = QTableWidget(0,2); self.table.setHorizontalHeaderLabels(['URL','Status'])
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # Save button
        save_layout = QHBoxLayout()
        self.save_btn = QPushButton('Save Results')
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_results)
        save_layout.addStretch()
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)

        # Logs
        self.log_box = QTextEdit(); self.log_box.setReadOnly(True); self.log_box.setMaximumHeight(180)
        layout.addWidget(QLabel('Log')); layout.addWidget(self.log_box)

    def load_wordlist(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open Wordlist', os.path.expanduser('~'))
        if path:
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                self.manual_text.setPlainText(content)
                self.log(f'Loaded wordlist: {path} ({len(content.splitlines())} lines)')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to load file: {e}')

    def start_scan(self):
        words = [w.strip() for w in self.manual_text.toPlainText().splitlines() if w.strip()]
        if not words:
            QMessageBox.warning(self,'No words','Provide words to scan.'); return
        url_template = self.tpl_input.text().strip();
        if 'ORG_NAME' not in url_template:
            QMessageBox.warning(self,'Template error','URL must contain ORG_NAME placeholder.'); return
        self._results.clear(); self.table.setRowCount(0); self.progress.setValue(0); self.log_box.clear()
        self.start_btn.setEnabled(False); self.stop_btn.setEnabled(True); self.load_btn.setEnabled(False); self.clear_btn.setEnabled(False)
        self._scanner = ScannerThread(words, url_template, self.workers_spin.value(), self.timeout_spin.value(), self.verify_ssl_cb.isChecked())
        self._scanner.progress.connect(self.progress.setValue); self._scanner.found.connect(self.add_result)
        self._scanner.log.connect(self.log); self._scanner.finished.connect(self.scan_finished)
        self._scanner.start()

    def stop_scan(self):
        if self._scanner: 
            self._scanner.stop()
            self.log('Stopping scan...')
            self.stop_btn.setEnabled(False)

    def add_result(self,url,code):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row,0,QTableWidgetItem(url))
        self.table.setItem(row,1,QTableWidgetItem(str(code)))
        self._results.append((url,code))
        self.save_btn.setEnabled(True)

    def scan_finished(self):
        self.log('Scan finished')
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.load_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)

    def save_results(self):
        if not self._results:
            QMessageBox.warning(self, 'No Data', 'No results to save.')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Save Results As', os.path.expanduser('~'), 'CSV Files (*.csv)')
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Status'])
                for row in self._results:
                    writer.writerow(row)
            self.log(f'Saved results to: {path}')
            QMessageBox.information(self, 'Saved', f'Results successfully saved to:\n{path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save file: {e}')

    def log(self,msg):
        self.log_box.append(msg)

    def _apply_professional_theme(self):
        qss = '''
        QWidget { background-color:#121212; color:#E0E0E0; font-family:'Segoe UI', Roboto; }
        QPushButton { background-color:#1DB954; border-radius:8px; padding:6px; color:white; font-weight:bold; }
        QPushButton:hover { background-color:#18a34a; }
        QPushButton:disabled { background-color:#2a2a2a; color:#7a7f86; }
        QLineEdit,QTextEdit,QSpinBox,QTableWidget { background-color:#1c1c1c; border:1px solid #333; border-radius:6px; padding:4px; }
        QHeaderView::section { background-color:#1a1a1a; padding:6px; border:none; }
        QProgressBar { background-color:#1c1c1c; border-radius:6px; text-align:center; }
        QProgressBar::chunk { background-color:#1DB954; }
        QTableWidget { gridline-color:#2a2a2a; }
        QLabel { color:#E0E0E0; font-weight:600; }
        QToolTip { background-color:#222; color:#ddd; }
        '''
        self.setStyleSheet(qss)

# -------------------- Entry Point --------------------
def main():
    app=QApplication(sys.argv)
    win=MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
