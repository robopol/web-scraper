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
        self.root.geometry("800x850")
        self.root.resizable(True, True)
        self.root.minsize(800, 850)
        
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
        self.url_var = tk.StringVar(value="https://yourdomain.com")
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
        
        # CSS download settings
        ttk.Label(self.advanced_tab, text="CSS:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        
        css_frame = ttk.Frame(self.advanced_tab)
        css_frame.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5, columnspan=3)
        
        self.download_css_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(css_frame, text="Download CSS styles", variable=self.download_css_var, 
                        command=self.toggle_css_options).pack(anchor=tk.W)
        
        self.css_frame_options = ttk.Frame(css_frame)
        self.css_frame_options.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.css_frame_options, text="Directory for CSS files:").pack(anchor=tk.W, pady=2)
        self.styles_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "scrap", "styles"))
        self.styles_dir_entry = ttk.Entry(self.css_frame_options, textvariable=self.styles_dir_var, width=50)
        self.styles_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=2)
        
        self.styles_dir_button = ttk.Button(self.css_frame_options, text="Select", command=self.select_styles_dir)
        self.styles_dir_button.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Disable CSS settings if not needed
        self.toggle_css_options()
        
        # JavaScript download settings
        ttk.Label(self.advanced_tab, text="JavaScript:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        
        js_frame = ttk.Frame(self.advanced_tab)
        js_frame.grid(row=4, column=1, sticky=tk.W, padx=10, pady=5, columnspan=3)
        
        self.download_js_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(js_frame, text="Download JavaScript files", variable=self.download_js_var, 
                        command=self.toggle_js_options).pack(anchor=tk.W)
        
        self.js_frame_options = ttk.Frame(js_frame)
        self.js_frame_options.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.js_frame_options, text="Directory for JavaScript files:").pack(anchor=tk.W, pady=2)
        self.scripts_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "scrap", "scripts"))
        self.scripts_dir_entry = ttk.Entry(self.js_frame_options, textvariable=self.scripts_dir_var, width=50)
        self.scripts_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=2)
        
        self.scripts_dir_button = ttk.Button(self.js_frame_options, text="Select", command=self.select_scripts_dir)
        self.scripts_dir_button.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Disable CSS and JS settings if not needed
        self.toggle_css_options()
        self.toggle_js_options()
        
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
        
        self.reset_button = ttk.Button(self.button_frame, text="Reset", command=self.reset_application)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
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
    
    def select_styles_dir(self):
        """Open dialog for selecting CSS directory"""
        directory = filedialog.askdirectory(initialdir=self.styles_dir_var.get())
        if directory:
            self.styles_dir_var.set(directory)
    
    def select_scripts_dir(self):
        """Open dialog for selecting JavaScript directory"""
        directory = filedialog.askdirectory(initialdir=self.scripts_dir_var.get())
        if directory:
            self.scripts_dir_var.set(directory)
    
    def toggle_image_options(self):
        """Enable/disable image settings based on checkbox"""
        if self.download_images_var.get():
            self.images_dir_entry.config(state=tk.NORMAL)
            self.images_dir_button.config(state=tk.NORMAL)
        else:
            self.images_dir_entry.config(state=tk.DISABLED)
            self.images_dir_button.config(state=tk.DISABLED)
    
    def toggle_css_options(self):
        """Enable/disable CSS settings based on checkbox"""
        if self.download_css_var.get():
            self.styles_dir_entry.config(state=tk.NORMAL)
            self.styles_dir_button.config(state=tk.NORMAL)
        else:
            self.styles_dir_entry.config(state=tk.DISABLED)
            self.styles_dir_button.config(state=tk.DISABLED)
    
    def toggle_js_options(self):
        """Enable/disable JavaScript settings based on checkbox"""
        if self.download_js_var.get():
            self.scripts_dir_entry.config(state=tk.NORMAL)
            self.scripts_dir_button.config(state=tk.NORMAL)
        else:
            self.scripts_dir_entry.config(state=tk.DISABLED)
            self.scripts_dir_button.config(state=tk.DISABLED)
    
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
        """Start scraping process"""
        if self.scraping_active:
            messagebox.showwarning("Running", "Scraping is already running.")
            return
        
        # Get parameters
        url = self.url_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        
        # Validate URL and output_dir
        if not url:
            messagebox.showerror("Error", "URL cannot be empty.")
            return
        
        if not output_dir:
            messagebox.showerror("Error", "Output directory cannot be empty.")
            return
        
        # Prepare JSON output path
        json_filename = self.json_file_var.get().strip()
        if not json_filename:
            json_filename = "scraped_data.json"
        
        if not json_filename.endswith('.json'):
            json_filename += '.json'
        
        json_path = os.path.join(output_dir, json_filename)
        
        # Get filtering parameters
        filter_eshop = self.filter_eshop_var.get()
        filter_english = self.filter_english_var.get()
        recursive = self.recursive_var.get()
        
        # Get advanced parameters
        request_delay = self.delay_var.get()
        url_include_patterns = self.get_include_patterns()
        url_exclude_patterns = self.get_exclude_patterns()
        
        # Image download settings
        download_images = False
        images_dir = None
        
        if self.download_images_var.get():
            download_images = True
            images_dir = self.images_dir_var.get().strip()
            
            # Create images directory if doesn't exist
            if images_dir and not os.path.exists(images_dir):
                try:
                    os.makedirs(images_dir, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create images directory: {e}")
                    return
        
        # CSS download settings
        download_css = False
        styles_dir = None
        
        if self.download_css_var.get():
            download_css = True
            styles_dir = self.styles_dir_var.get().strip()
            
            # Create styles directory if doesn't exist
            if styles_dir and not os.path.exists(styles_dir):
                try:
                    os.makedirs(styles_dir, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create styles directory: {e}")
                    return
        
        # JavaScript download settings
        download_js = False
        scripts_dir = None
        
        if self.download_js_var.get():
            download_js = True
            scripts_dir = self.scripts_dir_var.get().strip()
            
            # Create scripts directory if doesn't exist
            if scripts_dir and not os.path.exists(scripts_dir):
                try:
                    os.makedirs(scripts_dir, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create scripts directory: {e}")
                    return
        
        # Create and configure scraper
        self.scraper = RobopolScraper(
            output_dir=output_dir,
            base_url=url,
            status_callback=self.update_status,
            progress_callback=self.progress_callback_wrapper,
            filter_eshop=filter_eshop,
            filter_english=filter_english,
            recursive=recursive,
            request_delay=request_delay,
            url_include_patterns=url_include_patterns,
            url_exclude_patterns=url_exclude_patterns,
            download_images=download_images,
            images_dir=images_dir,
            download_css=download_css,
            download_js=download_js,
            styles_dir=styles_dir,
            scripts_dir=scripts_dir
        )
        
        # Update UI
        self.update_status("Starting scraper...")
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.progress_info_var.set("Processed: 0 / 0 URLs")
        
        # Disable/enable buttons
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Set flag
        self.scraping_active = True
        
        # Start scraper in separate thread
        self.scraper_thread = threading.Thread(target=self.run_scraper, args=(json_path,))
        self.scraper_thread.daemon = True
        self.scraper_thread.start()
    
    def run_scraper(self, json_path):
        """Function for scraper thread"""
        try:
            result = self.scraper.run_scraper(output_json=json_path)
            
            if result is True:  # Scraping completed successfully
                self.root.after(0, lambda: self.update_status(f"Scraping successfully completed. Results saved to {json_path}"))
            elif result is False:  # Scraping was stopped
                self.root.after(0, lambda: self.update_status("Scraping stopped by user."))
            else:  # Result is the JSON path or None in case of error
                self.root.after(0, lambda: self.update_status(f"Scraping completed. Results saved to {result}" if result else "Error during scraping"))
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
            
            # Request the scraper to stop
            if self.scraper:
                self.scraper.request_stop()
            
            # Set flag to prevent UI from accepting new scraping requests
            self.scraping_active = False
            
            # Note: We do not immediately restore UI elements
            # They will be restored when the scraper thread actually stops
            # by calling finish_scraping() from the run_scraper method
    
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
    
    def reset_application(self):
        """Reset application state for a new scraping session"""
        # Check if scraping is active
        if self.scraping_active:
            messagebox.showwarning("Warning", "Scraping is still running. Stop it first.")
            return
            
        # Reset progress bar and labels
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.progress_info_var.set("Processed: 0 / 0 URLs")
        self.status_label.config(text="Status: Ready")
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Release resources from previous scraper
        if self.scraper:
            self.scraper.close()
            self.scraper = None
        
        # Reset application state
        self.scraper_thread = None
        
        # Reset buttons
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Notify user
        self.log("Application reset. Ready for a new scraping session.")

def main():
    """Start the GUI application"""
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
