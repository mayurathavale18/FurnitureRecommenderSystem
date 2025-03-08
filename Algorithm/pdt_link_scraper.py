import os
import logging
import json
import re
from time import sleep
from random import randint
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Logging setup
logging.basicConfig(format="%(asctime)s - %(filename)s - %(message)s", level=logging.INFO)

# Define ROOT directory (adjust if needed)
script_dir = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("ROOT", script_dir)

# ChromeDriver path (Update this for Windows if necessary)
CHROMEDRIVER_PATH = "path/to/chromedriver.exe"  # Example: C:/chromedriver.exe (Windows)

# Website details
domain = "www.furniture.ca"
item_per_page = 24  # Items per page
categories = [
    "living-room-packages", "sofas", "loveseats", "sectionals",
    "chairs-chaises", "recliners", "ottomans-benches",
    "cabinets-shelving", "tv-stands-tv-mounts", "coffee-tables",
    "sofa-console-tables", "end-accent-tables"
]

def setup_driver():
    """Initializes and returns a headless Chrome WebDriver."""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

def scrape_category(driver, category, index):
    """Scrapes product links from a given category."""
    cat_links = []
    logging.info(f"Start scraping category: {category}")

    offset = item_per_page  # Pagination offset
    for i in range(10):  # Retry mechanism
        logging.info(f"Iteration {i}, Offset {offset}")

        link = f"https://www.furniture.ca/collections/furniture-living-room-{category}?offset={offset}"
        driver.get(link)

        # Wait for page to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
        except Exception as e:
            logging.warning(f"Page load timeout for {category}: {e}")
            continue

        # Parse page
        page = BeautifulSoup(driver.page_source, "html.parser")
        r = re.compile(r"/products/")  # Adjust regex if needed

        for a in page.findAll("a", href=r):
            link = a["href"]
            if link not in cat_links:
                logging.info(f"Found new link: {link}")
                cat_links.append(link)
            else:
                logging.warning("Duplicate link, skipping")

        # Pagination logic
        if len(cat_links) % item_per_page == 0 and len(cat_links) != 0:
            offset += item_per_page
        sleep(randint(10, 36))  # Random delay

    # Save category links
    product_link = {"category": category, "links": cat_links}
    with open(Path(ROOT, f"links_cat_{index}.json"), "w") as outfile:
        json.dump(product_link, outfile)
    
    logging.info(f"Finished scraping category: {category}")

def main():
    driver = setup_driver()

    # Scrape all categories
    for idx, category in enumerate(categories):
        scrape_category(driver, category, idx)

    driver.quit()  # Close WebDriver

    # Combine all category links
    logging.info("Combining all category links")
    product_links = []
    
    for i in range(len(categories)):
        with open(Path(ROOT, f"links_cat_{i}.json")) as infile:
            product_links.append(json.load(infile))
    
    with open(Path(ROOT, "product_links.json"), "w") as outfile:
        json.dump(product_links, outfile)
    
    logging.info("Scraping complete. All category links saved.")

if __name__ == "__main__":
    main()
