from scrapers.kawasaki_scraper import KawasakiScraper
import time
import logging
from pathlib import Path

def setup_logging():
    """Set up logging configuration"""
    log_dir = Path('data/raw/scraping_logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'scraping.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('KawasakiScraper')

def main():
    """Main function to run the scraper"""
    logger = setup_logging()
    logger.info("Starting Kawasaki motorcycle scraping process")
    
    try:
        scraper = KawasakiScraper()
        
        # Step 1: Save basic catalog data
        logger.info("Step 1: Saving basic catalog data...")
        scraper.save_categorized_data()
        logger.info("Basic catalog data saved successfully")
        
        # Step 2: Scrape full specifications for all models
        logger.info("Step 2: Starting full specification scraping...")
        
        # Get all motorcycle lines
        lines = scraper.get_motorcycle_lines()
        if not lines:
            logger.error("No motorcycle lines found!")
            return
        
        total_models = 0
        successful_scrapes = 0
        failed_scrapes = 0
        all_specs = []
        
        # Process each line
        for line in lines:
            logger.info(f"Processing line: {line}")
            
            # Get models for this line
            models = scraper.get_models_for_line(line)
            total_models += len(models)
            
            if not models:
                logger.warning(f"No models found for {line}")
                continue
            
            logger.info(f"Found {len(models)} models for {line}")
            
            # Process each model
            for model in models:
                try:
                    logger.info(f"Scraping specs for: {model['name']}")
                    specs = scraper.scrape_motorcycle_specs(model['url'])
                    
                    if specs:
                        all_specs.append(specs)
                        successful_scrapes += 1
                        logger.info(f"Successfully scraped specifications for {model['name']}")
                    else:
                        failed_scrapes += 1
                        logger.error(f"Failed to scrape specifications for {model['name']}")
                    
                    # Respect rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    failed_scrapes += 1
                    logger.error(f"Error scraping {model['name']}: {str(e)}")
                    continue
            
            logger.info(f"Completed processing {line} line")
            time.sleep(3)  # Longer delay between lines
        
        # Save the full specifications
        if all_specs:
            scraper.specs_data = all_specs
            scraper.save_to_json('kawasaki_full_specs.json')
            scraper.save_to_csv('kawasaki_full_specs.csv')
            
            # Print summary
            logger.info("\nScraping Summary:")
            logger.info("-" * 40)
            logger.info(f"Total models found: {total_models}")
            logger.info(f"Successfully scraped: {successful_scrapes}")
            logger.info(f"Failed to scrape: {failed_scrapes}")
            logger.info(f"Success rate: {(successful_scrapes/total_models)*100:.2f}%")
            
        else:
            logger.error("No specifications were successfully scraped!")
        
        logger.info("Scraping process completed!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        import traceback
        logger.error("Full error traceback:")
        logger.error(traceback.format_exc())
        
if __name__ == "__main__":
    main()