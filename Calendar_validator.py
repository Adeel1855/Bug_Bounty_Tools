import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import threading
import queue
import time
import csv
import re
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class CalendarEmailValidator:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Calendar Email Validator v1.0")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Email validation pattern
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # Results storage
        self.results = []
        self.running = False
        self.processed_count = 0
        self.total_emails = 0
        
        # Queue for thread-safe GUI updates
        self.update_queue = queue.Queue()
        
        # Setup GUI
        self.setup_gui()
        
        # Start checking for queue updates
        self.check_queue()
        
    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#f0f0f0')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, text="📅 Google Calendar Email Validator", 
                font=('Arial', 24, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack()
        
        tk.Label(header_frame, text="Validate if Google Calendar exists for email addresses", 
                font=('Arial', 12), bg='#f0f0f0', fg='#7f8c8d').pack()
        
        # Control Panel
        control_frame = tk.LabelFrame(main_frame, text="Controls", font=('Arial', 12, 'bold'),
                                     bg='#f0f0f0', fg='#2c3e50', padx=15, pady=15)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # File selection
        file_frame = tk.Frame(control_frame, bg='#f0f0f0')
        file_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(file_frame, text="Email List File:", font=('Arial', 11), 
                bg='#f0f0f0', width=15, anchor='w').pack(side=tk.LEFT)
        
        self.file_label = tk.Label(file_frame, text="No file selected", font=('Arial', 11),
                                  bg='white', relief=tk.SUNKEN, width=40, anchor='w', padx=10)
        self.file_label.pack(side=tk.LEFT, padx=(10, 5))
        
        tk.Button(file_frame, text="Browse", command=self.load_file,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                 relief=tk.RAISED, padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Settings frame
        settings_frame = tk.Frame(control_frame, bg='#f0f0f0')
        settings_frame.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(settings_frame, text="Threads:", font=('Arial', 11),
                bg='#f0f0f0', width=15, anchor='w').pack(side=tk.LEFT)
        
        self.threads_var = tk.StringVar(value="10")
        threads_spinbox = tk.Spinbox(settings_frame, from_=1, to=50, textvariable=self.threads_var,
                                    width=10, font=('Arial', 11))
        threads_spinbox.pack(side=tk.LEFT, padx=(10, 20))
        
        tk.Label(settings_frame, text="Delay (ms):", font=('Arial', 11),
                bg='#f0f0f0', width=10, anchor='w').pack(side=tk.LEFT)
        
        self.delay_var = tk.StringVar(value="100")
        delay_spinbox = tk.Spinbox(settings_frame, from_=0, to=5000, textvariable=self.delay_var,
                                  width=10, font=('Arial', 11), increment=100)
        delay_spinbox.pack(side=tk.LEFT, padx=(10, 0))
        
        # Button frame
        button_frame = tk.Frame(control_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=(15, 5))
        
        self.start_btn = tk.Button(button_frame, text="▶ Start Validation", command=self.start_validation,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                  relief=tk.RAISED, padx=20, pady=10, state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = tk.Button(button_frame, text="⏹ Stop", command=self.stop_validation,
                                 bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                                 relief=tk.RAISED, padx=20, pady=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_btn = tk.Button(button_frame, text="📊 Export Results", command=self.export_results,
                                   bg='#f39c12', fg='white', font=('Arial', 12, 'bold'),
                                   relief=tk.RAISED, padx=20, pady=10, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT)
        
        # Progress frame
        progress_frame = tk.Frame(main_frame, bg='#f0f0f0')
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_label = tk.Label(progress_frame, text="Ready", font=('Arial', 11),
                                      bg='#f0f0f0', fg='#2c3e50')
        self.progress_label.pack(anchor='w')
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=500, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Stats frame
        stats_frame = tk.Frame(main_frame, bg='#f0f0f0')
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.StringVar()
        self.stats_text.set("Valid: 0 | Invalid: 0 | Error: 0 | Total: 0")
        tk.Label(stats_frame, textvariable=self.stats_text, font=('Arial', 11, 'bold'),
                bg='#f0f0f0', fg='#2c3e50').pack()
        
        # Results display
        results_frame = tk.LabelFrame(main_frame, text="Validation Results", 
                                     font=('Arial', 12, 'bold'), bg='#f0f0f0', 
                                     fg='#2c3e50', padx=15, pady=15)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview with scrollbar
        tree_frame = tk.Frame(results_frame, bg='#f0f0f0')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('#', 'Email', 'Status', 'HTTP Code', 'Response Time', 'Details')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.tree.heading('#', text='#')
        self.tree.heading('Email', text='Email')
        self.tree.heading('Status', text='Status')
        self.tree.heading('HTTP Code', text='HTTP Code')
        self.tree.heading('Response Time', text='Response Time (ms)')
        self.tree.heading('Details', text='Details')
        
        # Define columns
        self.tree.column('#', width=50, anchor='center')
        self.tree.column('Email', width=200, anchor='w')
        self.tree.column('Status', width=100, anchor='center')
        self.tree.column('HTTP Code', width=80, anchor='center')
        self.tree.column('Response Time', width=120, anchor='center')
        self.tree.column('Details', width=300, anchor='w')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure tags for colors
        self.tree.tag_configure('valid', background='#d4edda', foreground='#155724')
        self.tree.tag_configure('invalid', background='#f8d7da', foreground='#721c24')
        self.tree.tag_configure('error', background='#fff3cd', foreground='#856404')
        self.tree.tag_configure('processing', background='#d1ecf1', foreground='#0c5460')
        
        # Log frame
        log_frame = tk.LabelFrame(main_frame, text="Log", font=('Arial', 12, 'bold'),
                                 bg='#f0f0f0', fg='#2c3e50', padx=15, pady=15)
        log_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=('Consolas', 9),
                                                 bg='#2c3e50', fg='#ecf0f1', insertbackground='white')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def check_queue(self):
        """Check for updates from worker threads"""
        try:
            while True:
                update = self.update_queue.get_nowait()
                if update[0] == 'result':
                    _, idx, email, status, http_code, response_time, details = update
                    self.add_result(idx, email, status, http_code, response_time, details)
                    self.processed_count += 1
                    self.update_progress()
                elif update[0] == 'stats':
                    valid, invalid, error = update[1:]
                    self.update_stats(valid, invalid, error)
                elif update[0] == 'log':
                    self.log_message(update[1], update[2])
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)
            
    def load_file(self):
        """Load email list from text file"""
        filename = filedialog.askopenfilename(
            title="Select Email List File",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Extract emails (one per line)
                self.emails = []
                for line in lines:
                    email = line.strip()
                    if email and not email.startswith('#'):
                        self.emails.append(email)
                
                self.total_emails = len(self.emails)
                self.file_label.config(text=f"{filename} ({self.total_emails} emails)")
                self.start_btn.config(state=tk.NORMAL)
                self.log_message(f"Loaded {self.total_emails} emails from {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
                
    def validate_email_format(self, email):
        """Validate email format using regex"""
        return bool(self.email_pattern.match(email))
    
    def check_calendar_url(self, email):
        """Check if Google Calendar exists for email"""
        url = f"https://calendar.google.com/calendar/u/0/htmlembed?src={email}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            response_time = int((time.time() - start_time) * 1000)  # Convert to ms
            
            # Check response
            if response.status_code == 200:
                # Check if it's a valid calendar or error page
                if "That's an error" in response.text or "was not found" in response.text:
                    return False, 404, response_time, "Calendar not found (404 in page content)"
                return True, 200, response_time, "Calendar exists"
            elif response.status_code == 404:
                return False, 404, response_time, "Calendar not found (404)"
            else:
                return False, response.status_code, response_time, f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, 0, 0, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, 0, 0, "Connection error"
        except Exception as e:
            return False, 0, 0, f"Error: {str(e)}"
    
    def validate_single_email(self, idx, email):
        """Validate a single email address"""
        # First validate email format
        if not self.validate_email_format(email):
            return idx, email, "INVALID", 0, 0, "Invalid email format"
        
        # Check calendar URL
        valid, http_code, response_time, details = self.check_calendar_url(email)
        
        status = "VALID" if valid else "INVALID"
        return idx, email, status, http_code, response_time, details
    
    def validation_worker(self):
        """Main validation worker running in thread"""
        self.running = True
        self.processed_count = 0
        self.results = []
        
        valid_count = 0
        invalid_count = 0
        error_count = 0
        
        # Log start
        self.update_queue.put(('log', f"Starting validation of {self.total_emails} emails...", "INFO"))
        
        try:
            max_workers = int(self.threads_var.get())
            delay_ms = int(self.delay_var.get())
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                
                for idx, email in enumerate(self.emails, 1):
                    if not self.running:
                        break
                    
                    # Submit task to thread pool
                    future = executor.submit(self.validate_single_email, idx, email)
                    futures.append(future)
                    
                    # Small delay to avoid overwhelming
                    if delay_ms > 0:
                        time.sleep(delay_ms / 1000)
                
                # Process results as they complete
                for future in as_completed(futures):
                    if not self.running:
                        break
                    
                    try:
                        idx, email, status, http_code, response_time, details = future.result()
                        
                        # Update counts
                        if status == "VALID":
                            valid_count += 1
                        elif status == "INVALID":
                            invalid_count += 1
                        else:
                            error_count += 1
                        
                        # Add to results
                        self.results.append({
                            'index': idx,
                            'email': email,
                            'status': status,
                            'http_code': http_code,
                            'response_time': response_time,
                            'details': details
                        })
                        
                        # Queue for GUI update
                        self.update_queue.put(('result', idx, email, status, http_code, response_time, details))
                        self.update_queue.put(('stats', valid_count, invalid_count, error_count))
                        
                    except Exception as e:
                        self.update_queue.put(('log', f"Error processing email: {str(e)}", "ERROR"))
                        
        except Exception as e:
            self.update_queue.put(('log', f"Validation error: {str(e)}", "ERROR"))
        finally:
            self.running = False
            self.update_queue.put(('log', f"Validation completed! Valid: {valid_count}, Invalid: {invalid_count}", "INFO"))
            
            # Update button states
            self.root.after(0, lambda: [
                self.start_btn.config(state=tk.NORMAL, text="▶ Start Validation"),
                self.stop_btn.config(state=tk.DISABLED),
                self.export_btn.config(state=tk.NORMAL),
                self.progress_bar.config(value=100)
            ])
    
    def start_validation(self):
        """Start validation process"""
        if not hasattr(self, 'emails') or not self.emails:
            messagebox.showwarning("Warning", "Please load an email file first!")
            return
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset counters
        self.processed_count = 0
        self.results = []
        
        # Update UI
        self.start_btn.config(state=tk.DISABLED, text="⏳ Processing...")
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        self.progress_bar.config(value=0)
        self.log_text.delete(1.0, tk.END)
        
        # Start validation in separate thread
        validation_thread = threading.Thread(target=self.validation_worker, daemon=True)
        validation_thread.start()
    
    def stop_validation(self):
        """Stop validation process"""
        self.running = False
        self.log_message("Stopping validation...", "INFO")
        self.stop_btn.config(state=tk.DISABLED)
    
    def add_result(self, idx, email, status, http_code, response_time, details):
        """Add result to treeview"""
        tags = ()
        if status == "VALID":
            tags = ('valid',)
        elif status == "INVALID":
            tags = ('invalid',)
        else:
            tags = ('error',)
        
        self.tree.insert('', 'end', values=(
            idx, email, status, http_code if http_code != 0 else "N/A", 
            response_time if response_time != 0 else "N/A", details
        ), tags=tags)
    
    def update_progress(self):
        """Update progress bar"""
        if self.total_emails > 0:
            progress = (self.processed_count / self.total_emails) * 100
            self.progress_bar['value'] = progress
            self.progress_label.config(text=f"Processed: {self.processed_count}/{self.total_emails} ({progress:.1f}%)")
    
    def update_stats(self, valid, invalid, error):
        """Update statistics display"""
        total = valid + invalid + error
        self.stats_text.set(f"✅ Valid: {valid} | ❌ Invalid: {invalid} | ⚠️ Error: {error} | 📊 Total: {total}")
    
    def export_results(self):
        """Export results to CSV file"""
        if not self.results:
            messagebox.showwarning("Warning", "No results to export!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            initialfile=f"calendar_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Index', 'Email', 'Status', 'HTTP_Code', 'Response_Time_ms', 'Details', 'Timestamp']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for result in self.results:
                        writer.writerow({
                            'Index': result['index'],
                            'Email': result['email'],
                            'Status': result['status'],
                            'HTTP_Code': result['http_code'],
                            'Response_Time_ms': result['response_time'],
                            'Details': result['details'],
                            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                
                self.log_message(f"Results exported to: {filename}", "INFO")
                messagebox.showinfo("Success", f"Results exported successfully!\n\nFile: {filename}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")

def main():
    root = tk.Tk()
    app = CalendarEmailValidator(root)
    root.mainloop()

if __name__ == "__main__":
    main()