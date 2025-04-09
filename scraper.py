#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import re
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request

# Logging system configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('RobopolScraper')

class RobopolScraper:
    """Class for scraping web pages from the robopol.sk domain."""
    
    def __init__(self, output_dir="scrap", base_url="your domain", 
                 status_callback=None, progress_callback=None,
                 filter_eshop=True, filter_english=True, recursive=True,
                 request_delay=0.0, url_include_patterns=None, url_exclude_patterns=None,
                 download_images=False, images_dir=None):
        """
        Initialization of the scraper.
        
        Args:
            output_dir (str): Directory for output files
            base_url (str): Base URL to start scraping from
            status_callback (callable): Function for recording status messages
            progress_callback (callable): Function for updating progress state
            filter_eshop (bool): Whether to filter e-shop pages
            filter_english (bool): Whether to filter English pages
            recursive (bool): Whether to recursively traverse pages
            request_delay (float): Delay between requests in seconds
            url_include_patterns (list): List of regex patterns for including URLs
            url_exclude_patterns (list): List of regex patterns for excluding URLs
            download_images (bool): Whether to download images from pages
            images_dir (str): Directory for downloaded images
        """
        self.output_dir = output_dir
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.status_callback = status_callback or self._default_status_callback
        self.progress_callback = progress_callback or self._default_progress_callback
        self.filter_eshop = filter_eshop
        self.filter_english = filter_english
        self.recursive = recursive
        self.request_delay = request_delay
        self.download_images = download_images
        self.images_dir = images_dir
        
        # Compile regex patterns for URL filters
        self.url_include_patterns = None
        if url_include_patterns:
            self.url_include_patterns = [re.compile(pattern) for pattern in url_include_patterns]
            
        self.url_exclude_patterns = None
        if url_exclude_patterns:
            self.url_exclude_patterns = [re.compile(pattern) for pattern in url_exclude_patterns]
        
        # Initialize sets for tracking visited URLs
        self.visited_urls = set()
        self.queue = set()
        self.skipped_urls = set()
        self.scraped_data = []
        
        # Scraping statistics
        self.stats = {
            'total_urls_processed': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'filtered_urls': 0,
            'downloaded_images': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Webdriver for dynamic pages (initialized later)
        self.driver = None
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        if download_images and images_dir:
            os.makedirs(images_dir, exist_ok=True)
    
    def _default_status_callback(self, message):
        """Default function for printing status messages."""
        logger.info(message)
        
    def _default_progress_callback(self, value):
        """Default function for updating progress state."""
        logger.info(f"Progress: {value}%")
    
    def _setup_webdriver(self):
        """Initialization and setup of webdriver for Selenium."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-logging")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.status_callback("Webdriver initialized")
            return True
        except Exception as e:
            self.status_callback(f"Error initializing webdriver: {e}")
            return False
    
    def close(self):
        """Close the webdriver and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.status_callback("Webdriver closed")
            except Exception as e:
                self.status_callback(f"Error closing webdriver: {e}")
    
    def get_page_content(self, url, use_selenium=False):
        """
        Get the HTML content of a page.
        
        Args:
            url (str): URL of the page to retrieve
            use_selenium (bool): Whether to use Selenium for JavaScript pages
            
        Returns:
            tuple: (soup, html_content) or (None, None) on error
        """
        try:
            if self.request_delay > 0:
                time.sleep(self.request_delay)
                
            if use_selenium:
                if not self.driver and not self._setup_webdriver():
                    return None, None
                
                self.driver.get(url)
                html_content = self.driver.page_source
            else:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    self.status_callback(f"Invalid server response: {response.status_code} for {url}")
                    return None, None
                html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup, html_content
        except Exception as e:
            self.status_callback(f"Error getting page content for {url}: {e}")
            return None, None
    
    def save_html_to_file(self, url, html_content):
        """
        Save HTML content to a file.
        
        Args:
            url (str): URL of the page
            html_content (str): HTML content to save
            
        Returns:
            str: Path to the saved file or None
        """
        try:
            parsed_url = urlparse(url)
            path_elements = parsed_url.path.strip('/').split('/')
            
            # Create directory structure based on URL path
            dir_path = self.output_dir
            if path_elements and path_elements[0]:
                dir_path = os.path.join(self.output_dir, *path_elements[:-1]) if len(path_elements) > 1 else self.output_dir
                os.makedirs(dir_path, exist_ok=True)
            
            # Filename
            filename = path_elements[-1] if path_elements and path_elements[-1] else "index"
            if not filename.endswith('.html'):
                filename = f"{filename}.html"
            
            file_path = os.path.join(dir_path, filename)
            
            # Save HTML content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return file_path
        except Exception as e:
            self.status_callback(f"Error saving HTML for {url}: {e}")
            return None
    
    def should_filter_url(self, url):
        """
        Check if a URL should be filtered.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if the URL should be filtered, False otherwise
        """
        # Domain check
        parsed_url = urlparse(url)
        if parsed_url.netloc != self.domain:
            return True
        
        # E-shop filtering
        if self.filter_eshop and ('/e-shop/' in url or '/eshop/' in url or '/shop/' in url):
            return True
        
        # English page filtering
        if self.filter_english and ('/en/' in url):
            return True
        
        # Filtering based on Include regex patterns
        if self.url_include_patterns:
            if not any(pattern.search(url) for pattern in self.url_include_patterns):
                return True
        
        # Filtering based on Exclude regex patterns
        if self.url_exclude_patterns:
            if any(pattern.search(url) for pattern in self.url_exclude_patterns):
                return True
        
        return False
    
    def extract_links(self, soup, current_url):
        """
        Extract all links from a page.
        
        Args:
            soup (BeautifulSoup): Analyzed page content
            current_url (str): Current URL for relative links
            
        Returns:
            list: List of URL links
        """
        links = []
        
        if not soup:
            return links
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip empty links, anchors, and JavaScript links
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Create absolute URL
            absolute_url = urljoin(current_url, href)
            
            # Remove fragments and parameters
            parsed_url = urlparse(absolute_url)
            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            
            # Add to list if not already processed and not filtered
            if clean_url not in self.visited_urls and clean_url not in self.queue:
                if not self.should_filter_url(clean_url):
                    links.append(clean_url)
                else:
                    self.skipped_urls.add(clean_url)
                    self.stats['filtered_urls'] += 1
        
        return links
    
    def download_images(self, soup, url):
        """
        Download images from a page and save them to a directory.
        
        Args:
            soup (BeautifulSoup): Analyzed page content
            url (str): URL of the page
            
        Returns:
            list: List of paths to downloaded images
        """
        if not self.download_images or not self.images_dir or not soup:
            return []
        
        downloaded_images = []
        
        try:
            parsed_url = urlparse(url)
            path_elements = parsed_url.path.strip('/').split('/')
            page_name = path_elements[-1] if path_elements and path_elements[-1] else "index"
            
            # Directory for images for this page
            page_images_dir = os.path.join(self.images_dir, page_name)
            os.makedirs(page_images_dir, exist_ok=True)
            
            # Find all img tags with src attribute
            for img_num, img_tag in enumerate(soup.find_all('img', src=True)):
                src = img_tag['src']
                if not src:
                    continue
                
                # Create absolute URL for the image
                img_url = urljoin(url, src)
                
                # Get filename
                img_filename = os.path.basename(urlparse(img_url).path)
                if not img_filename:
                    img_filename = f"image_{img_num}.jpg"
                
                # Target path for the image
                img_path = os.path.join(page_images_dir, img_filename)
                
                try:
                    # Download and save the image
                    if self.request_delay > 0:
                        time.sleep(self.request_delay)
                    
                    urllib.request.urlretrieve(img_url, img_path)
                    downloaded_images.append(img_path)
                    self.stats['downloaded_images'] += 1
                except Exception as e:
                    self.status_callback(f"Error downloading image {img_url}: {e}")
        except Exception as e:
            self.status_callback(f"Error processing images for {url}: {e}")
        
        return downloaded_images
    
    def scrape_url(self, url):
        """
        Scrape a single URL and return data and found links.
        
        Args:
            url (str): URL to scrape
            
        Returns:
            tuple: (data_dict, links) or (None, [])
        """
        self.status_callback(f"Processing: {url}")
        self.visited_urls.add(url)
        self.stats['total_urls_processed'] += 1
        
        # Get page content
        soup, html_content = self.get_page_content(url)
        if not soup or not html_content:
            self.stats['failed_scrapes'] += 1
            return None, []
        
        # Save HTML to file
        html_file = self.save_html_to_file(url, html_content)
        
        # Download images if enabled
        downloaded_images = []
        if self.download_images:
            downloaded_images = self.download_images(soup, url)
            self.status_callback(f"Downloaded {len(downloaded_images)} images for {url}")
        
        # Extract information
        title = soup.title.text if soup.title else "No Title"
        
        # Get content text
        content = ""
        main_content = soup.find("main") or soup.find("div", class_="content") or soup.find("article")
        if main_content:
            content = main_content.get_text(strip=True, separator=" ")
        else:
            content = soup.body.get_text(strip=True, separator=" ") if soup.body else ""
        
        # Create data dictionary
        data = {
            'url': url,
            'title': title,
            'html_file': html_file,
            'content_snippet': content[:500] + "..." if len(content) > 500 else content,
            'downloaded_images': downloaded_images
        }
        
        # Add to scraped data
        self.scraped_data.append(data)
        self.stats['successful_scrapes'] += 1
        
        # Find additional links if recursive
        links = []
        if self.recursive:
            links = self.extract_links(soup, url)
            self.status_callback(f"Found {len(links)} new links on {url}")
        
        return data, links
    
    def _update_progress(self, done_count, total_count):
        """Update progress bar based on the number of processed URLs."""
        if total_count > 0:
            progress = int((done_count / total_count) * 100)
            # Extended version of progress callback that also provides count data
            if callable(self.progress_callback):
                self.progress_callback(progress, done_count, total_count)
            else:
                logger.info(f"Progress: {progress}% ({done_count}/{total_count})")
            
    def run_scraper(self, output_json=None):
        """
        Start the scraping process from the base URL.
        
        Args:
            output_json (str): Path to output JSON file
            
        Returns:
            str: Path to output JSON file or None on error
        """
        try:
            self.status_callback(f"Starting scraping from {self.base_url}")
            self.stats['start_time'] = time.time()
            
            # Clear state from previous runs
            self.visited_urls.clear()
            self.queue.clear()
            self.skipped_urls.clear()
            self.scraped_data.clear()
            self.stats['total_urls_processed'] = 0
            self.stats['successful_scrapes'] = 0
            self.stats['failed_scrapes'] = 0
            self.stats['filtered_urls'] = 0
            self.stats['downloaded_images'] = 0
            
            # Start scraping from base URL
            self.queue.add(self.base_url)
            
            # Initialize progress bar at the beginning
            self._update_progress(0, 1)
            
            while self.queue:
                # Get next URL from queue
                url = self.queue.pop()
                
                # Scrape URL
                data, links = self.scrape_url(url)
                
                # Add new URLs to queue
                for link in links:
                    self.queue.add(link)
                
                # Update progress bar
                self._update_progress(len(self.visited_urls), len(self.visited_urls) + len(self.queue))
            
            # Completion
            self.stats['end_time'] = time.time()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            self.status_callback(f"Scraping completed. Processed {len(self.visited_urls)} URLs in {duration:.2f} seconds.")
            self.status_callback(f"Successful: {self.stats['successful_scrapes']}, " +
                               f"Failed: {self.stats['failed_scrapes']}, " +
                               f"Filtered: {self.stats['filtered_urls']}")
            
            if self.download_images:
                self.status_callback(f"Total images downloaded: {self.stats['downloaded_images']}")
            
            # Set progress to 100% and final counts
            self._update_progress(len(self.visited_urls), len(self.visited_urls))
            
            # Save results to JSON
            if output_json:
                with open(output_json, 'w', encoding='utf-8') as f:
                    json.dump({
                        'stats': {
                            'total_urls': len(self.visited_urls),
                            'successful_scrapes': self.stats['successful_scrapes'],
                            'failed_scrapes': self.stats['failed_scrapes'],
                            'filtered_urls': self.stats['filtered_urls'],
                            'downloaded_images': self.stats['downloaded_images'],
                            'duration_seconds': duration
                        },
                        'scraped_data': self.scraped_data
                    }, f, ensure_ascii=False, indent=2)
                
                self.status_callback(f"Results saved to {output_json}")
                return output_json
            
            return True
        except Exception as e:
            self.status_callback(f"Critical error during scraping: {e}")
            return None
        finally:
            # Close webdriver if used
            self.close()

def main():
    """Run scraper in standalone mode (without GUI)"""
    scraper = RobopolScraper(recursive=True)
    try:
        scraper.run_scraper()
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 