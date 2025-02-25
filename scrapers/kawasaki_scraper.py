from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin
from pathlib import Path
import json
import pandas as pd
import time
import re

class KawasakiScraper(BaseScraper):
    def __init__(self, config_path: str = 'config/config.yaml'):
        super().__init__(config_path)
        self.base_url = self.config['manufacturers']['kawasaki']['base_url']
        self.motorcycle_path = self.config['manufacturers']['kawasaki']['motorcycle_path']

    def get_motorcycle_lines(self) -> List[str]:
        '''Get motorcycle lines from the Motorcycle category only'''
        motorcycle_url = urljoin(self.base_url, self.motorcycle_path)
        response = self._make_request(motorcycle_url)

        if not response:
            self.logger.error("Failed to get motorcycle lines")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the motorcycle category section using just the data attribute
        subcategory_div = soup.find('div', attrs={'data-nav-sub-cat-id': '1'})
        
        if not subcategory_div:
            self.logger.error("Could not find motorcycle subcategory container")
            return []

        # Find all motorcycle lines within this section
        lines = []
        line_elements = subcategory_div.find_all('li', class_='list-inline-item', attrs={'data-item': 'subcat'})

        for element in line_elements:
            link = element.find('a', class_='nav-link')
            if link:
                line_name = link.get_text(strip=True)
                # Remove ®, ™, and other trademark symbols
                line_name = line_name.replace('®', '').replace('™', '').replace('℠', '').strip()
                # Remove any other special characters or extra whitespace
                line_name = ' '.join(line_name.split())
                if line_name:
                    lines.append(line_name)
                    self.logger.debug(f'Found motorcycle line: {line_name}')
        
        self.logger.info(f"Found {len(lines)} motorcycle lines: {', '.join(lines)}")
        return lines

    def get_models_for_line(self, line: str) -> List[Dict[str, str]]:
        """Get all models with their specification URLs for a motorcycle line"""
        motorcycle_url = urljoin(self.base_url, f"{self.motorcycle_path}/{line}")
        self.logger.debug(f"Fetching URL: {motorcycle_url}")
        response = self._make_request(motorcycle_url)
    
        if not response:
            self.logger.error(f"Failed to get models for line: {line}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        models = []
        seen_urls = set()

        # Define tab panel IDs for each line
        line_tab_ids = {
            'ninja': 'nav-tab-content-1',
            'z': 'nav-tab-content-16',
            'versys': 'nav-tab-content-4',
            'w': 'nav-tab-content-26',
            'eliminator': 'nav-tab-content-1004',
            'vulcan': 'nav-tab-content-14',
            'klr': 'nav-tab-content-1002',
            'klx': 'nav-tab-content-22',
            'kx': 'nav-tab-content-23'
    }

        # Get the tab ID for the current line
        tab_id = line_tab_ids.get(line.lower())
        if not tab_id:
            self.logger.error(f"No tab ID mapping found for line: {line}")
            return []

        # Find the specific tab panel for this line
        tab_panel = soup.find('div', id=tab_id)
        if not tab_panel:
            self.logger.error(f"Could not find tab panel with ID {tab_id} for line: {line}")
            return []

        # Find all product containers within this tab panel
        product_containers = tab_panel.find_all('div', class_='productRepeat')
        self.logger.debug(f"Found {len(product_containers)} product containers for line: {line}")

        for container in product_containers:
            try:
                # Get model navigation link
                model_link = container.find('a', attrs={'data-content': lambda x: x and 'Navigation Motorcycle' in str(x)})
                if not model_link:
                    continue

                base_href = model_link.get('href')
                if not base_href or base_href in seen_urls:
                    continue

                # Extract model info from the data-content attribute
                data_content = model_link.get('data-content', '')
                if not isinstance(data_content, str):
                    continue

                try:
                    content_parts = eval(data_content)
                    if len(content_parts) < 2:
                        continue
                    model_name = content_parts[1]
                except:
                    self.logger.error(f"Failed to parse data-content: {data_content}")
                    continue

                # Get the model page to find specification links
                model_url = urljoin(self.base_url, base_href)
                self.logger.debug(f"Fetching model page: {model_url}")
            
                model_response = self._make_request(model_url)
                if not model_response:
                    self.logger.error(f"Failed to get model page for: {model_name}")
                    continue

                model_soup = BeautifulSoup(model_response.text, 'html.parser')
            
                # Find specification links
                spec_links = model_soup.find_all('a', 
                                           class_='blackBtn',
                                           attrs={'aria-label': lambda x: x and 'VIEW SPECS & DETAILS' in str(x)})
            
                self.logger.debug(f"Found {len(spec_links)} spec links for model: {model_name}")
            
                for spec_link in spec_links:
                    spec_href = spec_link.get('href')
                    if not spec_href or spec_href in seen_urls:
                        continue

                    # Extract year and edition from the URL
                    url_parts = spec_href.split('/')
                    year_info = url_parts[-1].split('-')
                    year = year_info[0]
                    edition = '-'.join(year_info[1:]) if len(year_info) > 1 else 'base'
                
                    model_info = {
                        'name': f"{model_name} {year}",
                        'base_model': model_name,
                        'year': year,
                        'edition': edition,
                        'url': urljoin(self.base_url, spec_href),
                        'full_path': spec_href
                    }
                    models.append(model_info)
                    seen_urls.add(spec_href)
                    self.logger.debug(f"Added model: {model_info['name']} ({edition})")

                # Respect the delay between requests
                time.sleep(self.delay)

            except Exception as e:
                self.logger.error(f"Error processing model in {line}: {str(e)}")
                continue
    
        self.logger.info(f"Found {len(models)} models with specification URLs for line {line}")
        return models

    def scrape_motorcycle_specs(self, url: str) -> Optional[Dict]:
        """Scrape specifications for a specific motorcycle model"""
        response = self._make_request(url)
        
        if not response:
            return None
            
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract URL components for metadata
            url_parts = url.split('/')
            model_info = {
                'line': url_parts[-4],
                'style': url_parts[-3],
                'model': url_parts[-2],
                'year': url_parts[-1].split('-')[0],
                'edition': '-'.join(url_parts[-1].split('-')[1:]) if '-' in url_parts[-1] else None
            }
            
            specs = {
                'make': 'Kawasaki',
                **model_info,  # Include model information
                
            }

            spec_accordions = soup.find_all('div', class_='collapse specAccordion')

            for accordion in spec_accordions:
                category = accordion.get('data-accordion', '').lower()

                spec_table = accordion.find('table', class_='specTable')
                if not spec_table:
                    continue

                rows = spec_table.find_all('tr')
                for row in rows:
                    spec_name = row.find('th', class_='first')
                    spec_value = row.find('td')

                    if spec_name and spec_value:
                        name = spec_name.get_text(strip=True)
                        value = spec_value.get_text(strip=True)

                        key = f'{category}_{self._clean_key(name)}'
                        specs[key] = value

            
            self.logger.info(f"Successfully scraped specs for {model_info['year']} {model_info['model']}")
            return specs
            
        except Exception as e:
            self._log_error(url, str(e))
            return None
        
    def _clean_key(self, key : str) -> str:
        """Clean specification key names for consistent dictionary keys"""
        # Remove special characters and replace spaces with underscores
        clean = re.sub(r'[^\w\s]', '', key)
        clean = clean.lower().replace(' ', '_')
        return clean

    def _extract_spec(self, soup: BeautifulSoup, spec_name: str) -> Optional[str]:
        """Extract specific specification value"""
        spec_element = soup.find('dt', text=spec_name)
        if spec_element:
            value_element = spec_element.find_next('dd')
            return value_element.text.strip() if value_element else None
        return None

    def scrape_categorized_models(self) -> Dict[str, List[Dict[str, str]]]:
        """Scrape all motorcycle models categorized by their lines"""
        motorcycle_lines = self.get_motorcycle_lines()
        categorized_models = {}
        total_models = 0

        self.logger.info("Starting categorized model scraping")
        
        for line in motorcycle_lines:
            self.logger.info(f"Processing line: {line}")
            models = self.get_models_for_line(line)
            
            if models:
                categorized_models[line] = models
                total_models += len(models)
                self.logger.info(f"Found {len(models)} models for {line}")
        
        self.logger.info(f"Completed scraping. Total lines: {len(motorcycle_lines)}, Total models: {total_models}")
        return categorized_models
    

    def save_categorized_data(self, filename_prefix: str = 'kawasaki_catalog'):
        """Save categorized motorcycle data to both JSON and CSV formats"""
        categorized_data = self.scrape_categorized_models()
        
        # Save to JSON (preserves the hierarchical structure)
        json_filename = f"{filename_prefix}.json"
        output_path = Path(self.config['paths']['raw_data']) / json_filename
        with open(output_path, 'w') as f:
            json.dump(categorized_data, f, indent=4)
        self.logger.info(f"Saved categorized data to {json_filename}")
        
        # Save to CSV (flattened structure)
        csv_filename = f"{filename_prefix}.csv"
        output_path = Path(self.config['paths']['raw_data']) / csv_filename
        
        # Flatten the data for CSV
        flattened_data = []
        for line, models in categorized_data.items():
            for model in models:
                row = {
                    'line': line,
                    'model_name': model['name'],
                    'model_url': model['url'],
                    'full_path': model['full_path']
                }
                flattened_data.append(row)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_path, index=False)
        self.logger.info(f"Saved flattened data to {csv_filename}")

def main():
    try:
        scraper = KawasakiScraper()
        print("Starting Kawasaki motorcycle catalog scraping...")
        scraper.save_categorized_data()
        print("Scraping completed successfully!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()