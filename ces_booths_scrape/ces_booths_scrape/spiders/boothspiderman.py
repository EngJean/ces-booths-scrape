import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class BoothspidermanSpider(scrapy.Spider):
    name = "boothspiderman"
    allowed_domains = ["exhibitors.ces.tech"]
    start_urls = ["https://exhibitors.ces.tech/8_0/explore/exhibitor-gallery.cfm?featured=false"]

    def __init__(self):
        # Initialize Selenium WebDriver
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument('--headless')
        self.driver = webdriver.Firefox(options=firefox_options)

    def parse(self, response):
        # Use Selenium to navigate to the exhibitors page
        self.driver.get(response.url)

        try:
            # Wait for the "See All Results" button to be present and clickable
            see_all_results_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/main/div/section/div[2]/div/section/section/div[1]/span/a/span"))
            )

            # Click the button to load all results
            see_all_results_button.click()

            # Add a 5-second wait
            time.sleep(5)

            for i in range(1, 1560):  # Loop from 1 to 1547
                # Create a CSS selector for the current exhibitor card
                css_selector = f'li.js-Card:nth-child({i})'
                
                # Find the exhibitor card using the CSS selector
                card = self.driver.find_element(By.CSS_SELECTOR, css_selector)
                # Extract exhibitor name from each card
                exhibitor_name = card.find_element(By.CSS_SELECTOR, 'a').text.strip()

                # Click on the exhibitor's name link to access their info page
                exhibitor_link = card.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                if exhibitor_link:
                    yield scrapy.Request(url=exhibitor_link,
                                         callback=self.parse_exhibitor_info,
                                         meta={'Exhibitor Name': exhibitor_name})

        except Exception as e:
            self.logger.error(f"Error clicking 'See All Results' button: {e}")

    
    def parse_exhibitor_info(self, response):
        # Extract the exhibitor's name from the meta
        exhibitor_name = response.meta.get('Exhibitor Name')
        # Extract Booths, Description, and Product Categories
        booth_info = response.css('#scroll-boothlinks strong::text').getall()
        description = response.css('#scroll-description p.js-read-more::text').get()
        # product_categories = response.css('#scroll-products div[role="listitem"] h2 a::text').getall()
        # print(f"CATEGORIES FOUND: {product_categories}")

        # Remove unwanted characters from the scraped text
        booth_info = [booth.strip().replace('"', '').replace('\n', '').replace('\r', '') for booth in booth_info] if booth_info else ''
        description = description.strip().replace('"', '').replace('\n', '').replace('\r', '') if description else ''
        # product_categories = [category.strip().replace('"', '').replace('\n', '').replace('\r', '') for category in product_categories] if product_categories else ''

        # Yield the scraped data
        yield {
            'Exhibitor Name': exhibitor_name,
            'Booths': ', '.join(booth_info),
            'Description': description
        }


    def closed(self, reason):
        # Close the Selenium WebDriver when the spider is done
        self.driver.quit()
