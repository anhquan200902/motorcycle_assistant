# test_models.py
import sys
import os
import time
import json
import pandas as pd
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.kawasaki_scraper import KawasakiScraper

def test_line_extraction():
    """Test the extraction of motorcycle lines"""
    print("\nStarting motorcycle line extraction test...")
    print("=" * 80)
    
    try:
        scraper = KawasakiScraper()
        lines = scraper.get_motorcycle_lines()
        
        if not lines:
            print("No motorcycle lines found!")
            return
            
        print(f"Found {len(lines)} motorcycle lines:")
        for i, line in enumerate(lines, 1):
            print(f"{i}. {line}")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
    
    print("=" * 80)

def test_model_extraction():
    """Test the extraction of models for each line"""
    print("\nStarting model extraction test...")
    print("=" * 80)
    
    try:
        scraper = KawasakiScraper()
        
        # Get available lines
        lines = scraper.get_motorcycle_lines()
        
        if not lines:
            print("No motorcycle lines found!")
            return
            
        print(f"Found {len(lines)} motorcycle lines")
        
        # Print models and URLs for each line
        total_models = 0
        for line in lines:
            print(f"\nProcessing line: {line}")
            print("-" * 80)
            
            models = scraper.get_models_for_line(line)
            total_models += len(models)
            
            if models:
                print(f"Found {len(models)} models:\n")
                for i, model in enumerate(models, 1):
                    print(f"{i}. Model: {model['name']}")
                    print(f"   Base Model: {model['base_model']}")
                    print(f"   Year: {model['year']}")
                    print(f"   Edition: {model['edition']}")
                    print(f"   URL: {model['url']}")
                    print(f"   Path: {model['full_path']}")
                    print()
            else:
                print(f"No models found for {line}")
            
            print("-" * 80)
        
        print(f"\nTotal models across all lines: {total_models}")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
    
    print("=" * 80)

def test_data_saving():
    """Test saving the categorized data to files"""
    print("\nStarting data saving test...")
    print("=" * 80)
    
    try:
        scraper = KawasakiScraper()
        
        print("Saving categorized data...")
        scraper.save_categorized_data('test_kawasaki_catalog')
        
        # Verify files were created
        json_path = os.path.join('data', 'raw', 'test_kawasaki_catalog.json')
        csv_path = os.path.join('data', 'raw', 'test_kawasaki_catalog.csv')
        
        if os.path.exists(json_path):
            print(f"Successfully created JSON file: {json_path}")
            # Get file size
            size = os.path.getsize(json_path) / 1024  # Convert to KB
            print(f"JSON file size: {size:.2f} KB")
        else:
            print("Failed to create JSON file!")
            
        if os.path.exists(csv_path):
            print(f"Successfully created CSV file: {csv_path}")
            # Get file size
            size = os.path.getsize(csv_path) / 1024  # Convert to KB
            print(f"CSV file size: {size:.2f} KB")
        else:
            print("Failed to create CSV file!")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
    
    print("=" * 80)

def run_all_tests():
    """Run all test functions"""
    print("Starting all tests...")
    print("=" * 80)
    
    test_line_extraction()
    test_model_extraction()
    test_data_saving()
    
    print("\nAll tests completed!")


def test_spec_scraping():
    """Test the specification scraping functionality"""
    print("\nStarting specification scraping test...")
    print("=" * 80)
    
    try:
        scraper = KawasakiScraper()
        
        # Get one model to test
        lines = scraper.get_motorcycle_lines()
        if not lines:
            print("No motorcycle lines found!")
            return
            
        # Try to get Ninja models as a test case
        line = 'Ninja'
        print(f"\nFetching models for {line} line...")
        
        models = scraper.get_models_for_line(line)
        if not models:
            print(f"No models found for {line}!")
            return
            
        # Test spec scraping for the first model
        test_model = models[0]
        print(f"\nTesting spec scraping for: {test_model['name']}")
        print(f"URL: {test_model['url']}")
        print("-" * 80)
        
        specs = scraper.scrape_motorcycle_specs(test_model['url'])
        
        if specs:
            print("\nSuccessfully scraped specifications:")
            print("=" * 80)
            
            # Print metadata first
            metadata_fields = ['make', 'line', 'style', 'model', 'year', 'edition']
            print("\nMetadata:")
            print("-" * 40)
            for field in metadata_fields:
                if field in specs:
                    print(f"{field.title()}: {specs[field]}")
            
            # Print specifications by category
            categories = set(key.split('_')[0] for key in specs.keys() 
                           if '_' in key and key.split('_')[0] not in ['make', 'line', 'style', 'model', 'year'])
            
            for category in sorted(categories):
                print(f"\n{category.upper()} Specifications:")
                print("-" * 40)
                category_specs = {k: v for k, v in specs.items() 
                                if k.startswith(f"{category}_")}
                
                for key, value in sorted(category_specs.items()):
                    # Remove category prefix and clean up key name for display
                    display_key = key.replace(f"{category}_", '').replace('_', ' ').title()
                    print(f"{display_key}: {value}")
            
            print("\n" + "=" * 80)
        else:
            print("Failed to scrape specifications!")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
    
    print("=" * 80)


def test_full_spec_scraping():
    """Test scraping specifications for all models and save to files"""
    print("\nStarting full specification scraping test...")
    print("=" * 80)
    
    try:
        scraper = KawasakiScraper()
        all_specs = []
        
        # Get available lines
        lines = scraper.get_motorcycle_lines()
        if not lines:
            print("No motorcycle lines found!")
            return
        
        total_models = 0
        successful_scrapes = 0
        failed_scrapes = 0
        
        for line in lines:
            print(f"\nProcessing line: {line}")
            print("-" * 80)
            
            # Get models for this line
            models = scraper.get_models_for_line(line)
            total_models += len(models)
            
            if not models:
                print(f"No models found for {line}")
                continue
                
            print(f"Found {len(models)} models to process")
            
            # Process each model
            for model in models:
                try:
                    print(f"\nScraping specs for: {model['name']}")
                    specs = scraper.scrape_motorcycle_specs(model['url'])
                    
                    if specs:
                        all_specs.append(specs)
                        successful_scrapes += 1
                        print(f"Successfully scraped specifications for {model['name']}")
                    else:
                        failed_scrapes += 1
                        print(f"Failed to scrape specifications for {model['name']}")
                        
                    # Respect rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    failed_scrapes += 1
                    print(f"Error scraping {model['name']}: {str(e)}")
                    continue
            
            print(f"\nCompleted processing {line} line")
            time.sleep(3)  # Longer delay between lines
        
        # Save results if we have any
        if all_specs:
            # Create data directory if it doesn't exist
            data_dir = Path('data/raw')
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON
            json_path = data_dir / 'kawasaki_full_specs.json'
            with open(json_path, 'w') as f:
                json.dump(all_specs, f, indent=4)
            print(f"\nSaved specifications to {json_path}")
            
            # Save to CSV
            csv_path = data_dir / 'kawasaki_full_specs.csv'
            df = pd.DataFrame(all_specs)
            df.to_csv(csv_path, index=False)
            print(f"Saved specifications to {csv_path}")
            
            # Print summary
            print("\nScraping Summary:")
            print("-" * 40)
            print(f"Total models found: {total_models}")
            print(f"Successfully scraped: {successful_scrapes}")
            print(f"Failed to scrape: {failed_scrapes}")
            print(f"Success rate: {(successful_scrapes/total_models)*100:.2f}%")
            
        else:
            print("\nNo specifications were successfully scraped!")
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
    
    print("=" * 80)


if __name__ == "__main__":
    test_full_spec_scraping()