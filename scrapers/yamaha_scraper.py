from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin
from pathlib import Path
import json
import pandas as pd
import time
import re

class YamahaScraper(BaseScraper):
    def __init__(self, config_path = 'config/config.yaml'):
        super().__init__(config_path)
        self.base_url = self.config['manufacturers']['yamaha']['base_url']
        self.categories = self.config['manufacturers']['yamaha']['categories']
    
    def get_motorcycle_catalog(self) -> Dict[str, List[str]]:
        catalog = {}

        for category_name, category_path in self.categories.items():
            self.logger.info(f"Fetching {category_name} motorcycles...")
            category_url = urljoin(self.base_url, category_path)
            response = self._make_request(category_url)

            if not response:
                self.logger.error(f'Failed to get {category_name} motorcycles.')
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            models = self._extract_models_from_page(soup, category_name)

            if models:
                subcategories = {}
                for model in models:
                    subcategory = model['subcategory']
                    if subcategory not in subcategories:
                        subcategories[subcategory] = []
                    subcategories[subcategory].append(model)

                catalog[category_name] = subcategories
                self.logger.info(f"Found {len(models)} in {category_name} category.")
            else:
                self.logger.warning(f"No models found for {category_name} category.")

            time.sleep(self.delay)

        return catalog

    def _extract_models_from_page(self, soup: BeautifulSoup, category: str) -> List[Dict[str, str]]:
        """Extract models from a category page"""
        models = []
    
        product_catalog = soup.find('div' ,id="product_list")
        if not product_catalog:
            self.logger.error(f"Could not find product_list div in {category} page")
            return models
        
        products = product_catalog.find_all('div[class="mb-2 text-left"]')
    
        self.logger.info(f"Found {len(products)} products in {category} page")
    
        for product in products:
            try:
                # Find the model link
                model_link = product.find('a')
                if not model_link or not model_link.has_attr('href'):
                    continue
                
                model_url = model_link['href']
            
                # Extract just the model name from the link text or nearby elements
                model_name = model_link.text.strip()
                if not model_name:
                    # Fallback to get model name from URL
                    model_name = model_url.split('/')[-1].replace('-', ' ').title()
            
                # Create simple model info dictionary
                model_info = {
                    'name': model_name,
                    'category': category,
                    'url': urljoin(self.base_url, model_url),
                    'full_path': model_url
                }
            
                models.append(model_info)
                self.logger.debug(f"Found model: {model_info['name']} at {model_info['url']}")
            
            except Exception as e:
                self.logger.error(f"Error processing model in {category}: {str(e)}")
                continue
    
        self.logger.info(f"Extracted {len(models)} models from {category} page")
        return models
    
    def scrape_motorcycle_specs(self, url: str) -> Optional[Dict]:
        """Scrape specifications for a specific motorcycle model"""
        # This is a placeholder implementation to satisfy the abstract method requirement
        # Will be properly implemented later
        self.logger.info(f"Placeholder for scraping specs from {url}")
    
        # Return a minimal dictionary with the URL
        return {
            'make': 'Yamaha',
            'url': url,
            'specs_status': 'not_implemented_yet'
        }
            



