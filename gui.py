import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import json
import re
import time
from scraper import RobopolScraper

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RobopolScraper - Web Extractor")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        # State variables
        self.scraping_active = False
        self.scraper_thread = None
        self.scraper = None
        
        # Create main frames
        self.create_notebook()
        self.create_progress_frame()
        self.create_control_buttons()
        
        # Styling
        self.style = ttk.Style()
        self.style.configure("TNotebook", background="#f0f0f0")
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Start.TButton", background="green", font=("Arial", 10, "bold"))
        self.style.configure("Stop.TButton", background="red", font=("Arial", 10, "bold"))
        
        # Initialize log window
        self.log("RobopolScraper application ready")
        self.log("Enter URL, select output directory and click 'Start scraping'")
    
    def create_notebook(self):
        """Create tabs with settings"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab with basic settings
        self.basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_tab, text="Basic Settings")
        
        # Tab with advanced settings
        self.advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.advanced_tab, text="Advanced Settings")
        
        self.setup_basic_tab()
        self.setup_advanced_tab()
    
    def setup_basic_tab(self):
        """Set up components on the basic settings tab"""
        # URL input
        ttk.Label(self.basic_tab, text="Page URL:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.url_var = tk.StringVar(value="https://robopol.sk")
        ttk.Entry(self.basic_tab, textvariable=self.url_var, width=60).grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5, columnspan=2)
        
        # Output directory
        ttk.Label(self.basic_tab, text="Output directory:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.output_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "scrap"))
        ttk.Entry(self.basic_tab, textvariable=self.output_dir_var, width=50).grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)
        ttk.Button(self.basic_tab, text="Select", command=self.select_output_dir).grid(row=1, column=2, padx=5, pady=5)
        
        # Output JSON file
        ttk.Label(self.basic_tab, text="JSON file:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.json_file_var = tk.StringVar(value="scraped_data.json")
        ttk.Entry(self.basic_tab, textvariable=self.json_file_var, width=50).grid(row=2, column=1, sticky=tk.EW, padx=10, pady=5, columnspan=2)
        
        # Basic filtering options
        ttk.Label(self.basic_tab, text="Basic filters:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        
        filter_frame = ttk.Frame(self.basic_tab)
        filter_frame.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        self.filter_eshop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Filter e-shop pages", variable=self.filter_eshop_var).pack(anchor=tk.W)
        
        self.filter_english_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Filter English pages", variable=self.filter_english_var).pack(anchor=tk.W)
        
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Recursively traverse links", variable=self.recursive_var).pack(anchor=tk.W)
        
        # Set dynamic layout
        self.basic_tab.columnconfigure(1, weight=1)
    
    def setup_advanced_tab(self):
        """Set up components on the advanced settings tab"""
        # Speed setting
        ttk.Label(self.advanced_tab, text="Delay (s):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.delay_var = tk.DoubleVar(value=0.0)
        delay_entry = ttk.Spinbox(self.advanced_tab, from_=0.0, to=10.0, increment=0.1, textvariable=self.delay_var, width=10)
        delay_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        ttk.Label(self.advanced_tab, text="Delay between server requests").grid(row=0, column=2, sticky=tk.W, padx=10, pady=5)
        
        # URL filtering using regex
        ttk.Label(self.advanced_tab, text="URL filters:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        filter_frame = ttk.Frame(self.advanced_tab)
        filter_frame.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5, columnspan=3)
        
        ttk.Label(filter_frame, text="Include URLs (regex):").pack(anchor=tk.W, pady=2)
        self.url_include_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.url_include_var, width=50).pack(fill=tk.X, pady=2)
        ttk.Label(filter_frame, text="Example: .*blog.*|.*news.* (for blog and news)").pack(anchor=tk.W, pady=0)
        
        ttk.Label(filter_frame, text="Exclude URLs (regex):").pack(anchor=tk.W, pady=2)
        self.url_exclude_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.url_exclude_var, width=50).pack(fill=tk.X, pady=2)
        ttk.Label(filter_frame, text="Example: .*product.*|.*contact.* (exclude products and contact)").pack(anchor=tk.W, pady=0)
        
        # Image download settings
        ttk.Label(self.advanced_tab, text="Images:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        
        images_frame = ttk.Frame(self.advanced_tab)
        images_frame.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5, columnspan=3)
        
        self.download_images_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(images_frame, text="Download images", variable=self.download_images_var, 
                        command=self.toggle_image_options).pack(anchor=tk.W)
        
        self.images_frame_options = ttk.Frame(images_frame)
        self.images_frame_options.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.images_frame_options, text="Directory for images:").pack(anchor=tk.W, pady=2)
        self.images_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "scrap", "images"))
        self.images_dir_entry = ttk.Entry(self.images_frame_options, textvariable=self.images_dir_var, width=50)
        self.images_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=2)
        
        self.images_dir_button = ttk.Button(self.images_frame_options, text="Select", command=self.select_images_dir)
        self.images_dir_button.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Disable image settings if not needed
        self.toggle_image_options()
        
        # Set dynamic layout
        self.advanced_tab.columnconfigure(1, weight=1)
    
    def create_progress_frame(self):
        """Create frame with progress bar and log window"""
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Progress bar
        progress_header = ttk.Frame(self.progress_frame)
        progress_header.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(progress_header, text="Progress:").pack(side=tk.LEFT, padx=5)
        
        # Information about processed URLs
        self.progress_info_var = tk.StringVar(value="Processed: 0 / 0 URLs")
        ttk.Label(progress_header, textvariable=self.progress_info_var).pack(side=tk.RIGHT, padx=5)
        
        # Progress bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100, length=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Status indicator
        self.status_frame = ttk.Frame(self.progress_frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.status_label = ttk.Label(self.status_frame, text="Status: Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_label = ttk.Label(self.status_frame, text="0%")
        self.progress_label.pack(side=tk.RIGHT)
        
        # Log window
        ttk.Label(self.progress_frame, text="Log:").pack(anchor=tk.W, padx=5, pady=2)
        self.log_text = scrolledtext.ScrolledText(self.progress_frame, height=10, wrap=tk.WORD, background="black", foreground="#00FF00")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
    
    def create_control_buttons(self):
        """Create control buttons"""
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(self.button_frame, text="Start scraping", command=self.start_scraping, style="Start.TButton")
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="Stop", command=self.stop_scraping, style="Stop.TButton", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.button_frame, text="Close", command=self.close_application).pack(side=tk.RIGHT, padx=5)
    
    def log(self, message):
        """Write message to log window"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """Update status text"""
        self.status_label.config(text=f"Status: {message}")
        self.log(message)
    
    def update_progress(self, value, current_count=None, total_count=None):
        """Update progress bar and progress information"""
        self.progress_var.set(value)
        self.progress_label.config(text=f"{value}%")
        
        # If count information is provided, update it
        if current_count is not None and total_count is not None:
            self.progress_info_var.set(f"Processed: {current_count} / {total_count} URLs")
        
        # If 100%, set status to completed
        if value >= 100:
            self.update_status("Completed")
            
            # Enable Start button and disable Stop button
            if self.scraping_active:
                self.scraping_active = False
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
    
    def select_output_dir(self):
        """Open dialog for selecting output directory"""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def select_images_dir(self):
        """Open dialog for selecting images directory"""
        directory = filedialog.askdirectory(initialdir=self.images_dir_var.get())
        if directory:
            self.images_dir_var.set(directory)
    
    def toggle_image_options(self):
        """Enable/disable image settings based on checkbox"""
        if self.download_images_var.get():
            self.images_dir_entry.config(state=tk.NORMAL)
            self.images_dir_button.config(state=tk.NORMAL)
        else:
            self.images_dir_entry.config(state=tk.DISABLED)
            self.images_dir_button.config(state=tk.DISABLED)
    
    def get_include_patterns(self):
        """Process regex pattern for including URLs"""
        include_text = self.url_include_var.get().strip()
        if not include_text:
            return None
        
        try:
            # Try to compile regex to verify it's valid
            re.compile(include_text)
            return [include_text]
        except re.error:
            self.log(f"Invalid regex pattern for inclusion: {include_text}")
            return None
    
    def get_exclude_patterns(self):
        """Process regex pattern for excluding URLs"""
        exclude_text = self.url_exclude_var.get().strip()
        if not exclude_text:
            return None
        
        try:
            # Try to compile regex to verify it's valid
            re.compile(exclude_text)
            return [exclude_text]
        except re.error:
            self.log(f"Invalid regex pattern for exclusion: {exclude_text}")
            return None
    
    def start_scraping(self):
        """Start scraping process in a new thread"""
        # URL check
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "You must enter a URL")
            return
        
        # Set output directory
        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showerror("Error", "You must enter an output directory")
            return
        
        # Option to use custom directory for images
        images_dir = None
        if self.download_images_var.get():
            images_dir = self.images_dir_var.get().strip()
            if not images_dir:
                messagebox.showerror("Error", "You must enter a directory for images")
                return
        
        # Set output JSON file
        json_file = self.json_file_var.get().strip()
        if not json_file:
            json_file = "scraped_data.json"
        
        if not json_file.endswith('.json'):
            json_file += '.json'
        
        json_path = os.path.join(output_dir, json_file)
        
        # Create directories if they don't exist
        os.makedirs(output_dir, exist_ok=True)
        if images_dir:
            os.makedirs(images_dir, exist_ok=True)
        
        # Get URL regex patterns
        include_patterns = self.get_include_patterns()
        exclude_patterns = self.get_exclude_patterns()
        
        # Disable Start button, enable Stop button
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Set progress bar to 0
        self.update_progress(0, 0, 0)
        self.update_status("Starting scraper...")
        
        # Set flag that scraping is running
        self.scraping_active = True
        
        # Initialize scraper with custom progress callback for more detailed information
        self.scraper = RobopolScraper(
            output_dir=output_dir,
            base_url=url,
            status_callback=self.update_status,
            progress_callback=self.progress_callback_wrapper,
            filter_eshop=self.filter_eshop_var.get(),
            filter_english=self.filter_english_var.get(),
            recursive=self.recursive_var.get(),
            request_delay=self.delay_var.get(),
            url_include_patterns=include_patterns,
            url_exclude_patterns=exclude_patterns,
            download_images=self.download_images_var.get(),
            images_dir=images_dir
        )
        
        # Start in a new thread
        self.scraper_thread = threading.Thread(target=self.run_scraper, args=(json_path,))
        self.scraper_thread.daemon = True
        self.scraper_thread.start()
    
    def run_scraper(self, json_path):
        """Function for scraper thread"""
        try:
            result = self.scraper.run_scraper(output_json=json_path)
            
            if result:
                self.root.after(0, lambda: self.update_status(f"Scraping successfully completed. Results saved to {json_path}"))
            else:
                self.root.after(0, lambda: self.update_status("Error during scraping"))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Critical error: {e}"))
        finally:
            # Stop scraper and clean up
            if self.scraper:
                self.scraper.close()
            
            # Restore UI elements
            self.root.after(0, lambda: self.finish_scraping())
    
    def stop_scraping(self):
        """Stop scraping process"""
        if self.scraping_active:
            self.update_status("Stopping scraping...")
            self.scraping_active = False
            
            # Terminate scraper
            if self.scraper:
                self.scraper.close()
            
            # Restore UI elements
            self.finish_scraping()
    
    def finish_scraping(self):
        """Restore UI elements after completion/stopping scraping"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Scraper stopped")
    
    def close_application(self):
        """Close the application"""
        if self.scraping_active:
            if messagebox.askyesno("Close", "Scraping is still running. Do you really want to close the application?"):
                self.stop_scraping()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def progress_callback_wrapper(self, value, current_count=None, total_count=None):
        """Wrapper for progress callback that adds additional URL count information"""
        # We need to use after because this function is called from another thread
        self.root.after(0, lambda: self.update_progress(value, current_count, total_count))

def main():
    """Start the GUI application"""
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 