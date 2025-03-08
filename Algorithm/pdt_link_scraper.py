import os
import logging
import json
import re
from time import sleep
from random import randint
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logging.basicConfig(format='%(asctime)s - %(filename)s - %(message)s', level=logging.INFO)

# Set up root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
default_root = os.path.dirname(script_dir)
ROOT = os.environ.get("ROOT", default_root)

domain = "www.furniture.ca"
item_per_page = 24
categories = ["living-room-packages", "sofas", "loveseats", "sectionals", "chairs-chaises", "recliners",
              "ottomans-benches", "cabinets-shelving", "tv-stands-tv-mounts", "coffee-tables",
              "sofa-console-tables", "end-accent-tables"]

def main():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Disable for debugging
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    for k, cat in enumerate(categories):
        cat_links = []
        logging.info(f"Start scraping category {cat}")
        offset = 0  # Start from 0 instead of item_per_page

        for i in range(10):  # Retry scraping up to 10 times
            logging.info(f"Start iteration {i}, Offset {offset}")
            link = f"https://www.furniture.ca/collections/furniture-living-room-{cat}?offset={offset}"
            driver.get(link)

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                logging.warning("Page did not load properly")
                continue  # Skip this iteration if page didn't load

            page = BeautifulSoup(driver.page_source, "html.parser")
            r = re.compile(r"myshopify.com/products")

            for a in page.findAll("a", href=r):
                product_link = a["href"]
                if product_link not in cat_links:
                    logging.info(f"Found new link {product_link}")
                    cat_links.append(product_link)

            if len(cat_links) % item_per_page == 0 and len(cat_links) > 0:
                offset += item_per_page  # Move to next page

            logging.info(f"Collected {len(cat_links)} items")
            sleep(randint(2, 6))  # Reduce sleep time

        with open(Path(ROOT, f"links_cat_{k}.json"), "w") as outfile:
            json.dump({"category": cat, "links": cat_links}, outfile)

        logging.info(f"Finish scraping category {cat}")

    logging.info("Start combining all category links")
    all_product_links = []

    for i in range(len(categories)):
        with open(Path(ROOT, f"links_cat_{i}.json")) as infile:
            all_product_links.append(json.load(infile))

    with open(Path(ROOT, "product_links.json"), "w") as outfile:
        json.dump(all_product_links, outfile)

    logging.info("Finish combining all category links")
    driver.quit()

if __name__ == "__main__":
    main()
