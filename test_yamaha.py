# test_yamaha.py
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.yamaha_scraper import YamahaScraper
from bs4 import BeautifulSoup
import requests

def test_model_extraction():
    """Test the extraction of models from Yamaha's website"""
    print("\nStarting Yamaha model extraction test...")
    print("=" * 80)
    
    try:
        scraper = YamahaScraper()
        
        # Test for each category (road and off-road)
        for category_name, category_path in scraper.categories.items():
            print(f"\nTesting {category_name} category extraction...")
            print("-" * 60)
            
            url = scraper.base_url + category_path
            print(f"URL: {url}")
            
            # Make the request
            response = scraper._make_request(url)
            
            if not response:
                print(f"Failed to load {category_name} page!")
                continue
                
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product catalog
            product_catalog = soup.find('div', id='product_list')
            if not product_catalog:
                print(f"Could not find product_list div in {category_name} page")
                print("Available div classes:")
                for div in soup.find_all('div', class_=True):
                    print(f"  - {div.get('class')}")
                continue
                
            print(f"Found product_list container: {product_catalog.name}")
            
            # Find products
            products = product_catalog.find_all('div', class_="mb-2 text-left")
            
            if not products:
                print(f"No products found with class='mb-2 text-left'")
                print("Looking for alternatives...")
                
                # Try different CSS selector approach
                products = soup.select('div.mb-2.text-left')
                if products:
                    print(f"Found {len(products)} products using CSS selector")
                else:
                    print("Still no products found. Dumping some sample divs:")
                    for i, div in enumerate(product_catalog.find_all('div', class_=True)[:5]):
                        print(f"{i+1}. Class: {div.get('class')}, Text: {div.text[:50]}...")
                    continue
            
            print(f"Found {len(products)} products")
            
            # Process first 5 products as a sample
            print("\nSample products:")
            for i, product in enumerate(products[:5]):
                try:
                    model_link = product.find('a')
                    if not model_link or not model_link.has_attr('href'):
                        print(f"{i+1}. No valid link found")
                        continue
                        
                    model_url = model_link['href']
                    model_name = model_link.text.strip()
                    
                    print(f"{i+1}. Model: {model_name}")
                    print(f"   URL: {model_url}")
                    print()
                except Exception as e:
                    print(f"{i+1}. Error processing: {str(e)}")
            
            # Respect rate limiting
            time.sleep(2)
            
        print("\nTest completed!")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
    
    print("=" * 80)

def test_full_catalog():
    """Test getting the full motorcycle catalog"""
    print("\nStarting full catalog test...")
    print("=" * 80)
    
    try:
        scraper = YamahaScraper()
        catalog = scraper.get_motorcycle_catalog()
        
        if not catalog:
            print("No catalog data returned!")
            return
            
        print("\nCatalog summary:")
        for category, subcategories in catalog.items():
            print(f"\nCategory: {category}")
            print("-" * 40)
            
            total_models = sum(len(models) for models in subcategories.values())
            print(f"Total models: {total_models}")
            
            for subcategory, models in subcategories.items():
                print(f"  {subcategory}: {len(models)} models")
                
                # Show first model in each subcategory as example
                if models:
                    print(f"    Example: {models[0]['name']} - {models[0]['url']}")
        
        print("\nFull catalog retrieved successfully!")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
    
    print("=" * 80)

if __name__ == "__main__":
    # Test model extraction
    test_model_extraction()