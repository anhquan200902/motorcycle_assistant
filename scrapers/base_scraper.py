import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import logging
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
import yaml
from pathlib import Path

class BaseScraper(ABC):
    def __init__(self, config_path: str = 'config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self._setup_logging()

        self.headers = {
            'User-Agent': self.config['scraping']['user_agent']
        }

        self.specs_data = []
        self.delay = self.config['scraping']['delay']

    def _setup_logging(self):
        '''Setup logging configurations'''
        log_path = Path(self.config['paths']['logs'])
        log_path.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=self.config['logging']['level'],
            format=self.config['logging']['format'],
            handlers=[
                logging.FileHandler(log_path / 'scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def scrape_motorcycle_specs(self, url : str) -> Optional[Dict]:
        pass

    def save_to_csv(self, filename : str) -> None:
        '''Save scraped files to CSV'''
        output_path = Path(self.config['paths']['raw_data']) / filename
        df = pd.DataFrame(self.specs_data)
        df.to_csv(output_path, index=False)
        self.logger.info(f'Data saved to {output_path}')

    def save_to_json(self, filename : str) -> None:
        '''Save scraped data to JSON file'''
        output_path = Path(self.config['paths']['raw_data']) / filename
        with open(output_path, 'w') as f:
            json.dump(self.specs_data, f, indent=4)
        self.logger.info(f'Data saved to {output_path}')
    
    def _make_request(self, url : str) -> Optional[requests.Response]:
        '''Make HTTP request with retry logic'''
        for attempt in range(self.config['scraping']['retries']):
            try:
                time.sleep(self.delay)
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response
            except Exception as e:
                self.logger.error(f'Attempt {attempt + 1} failed for {url}: {str(e)}')
                if attempt == self.config['scraping']['retries'] - 1:
                    self.logger.error(f'All attempts failed for {url}')
                    return None
        return None
    
    def _log_error(self, url : str, error : str) -> None:
        '''Log errors for debugging'''
        self.logger.error(f"Error scraping {url}: {error}")
        