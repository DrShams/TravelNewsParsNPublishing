import os
import logging
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

class HTMLParser:
    """Class for parsing HTML content from a webpage."""

    def __init__(self, url):
        """Initialize the HTMLParser."""
        self.url = url
        self.extracted_info = {}
        self.html_content = None
        self.image_filename = None

    def fetch_html_content(self):
        """Fetch the HTML content."""
        response = requests.get(self.url, timeout=60)
        time.sleep(3)
        self.html_content = response.content
        logging.info(f'Content HTML was received with url \n{self.url}')
        logging.debug(self.html_content)

    def parse_html_news(self, news_age_limit_days):
        """Parse the HTML content and validate the news based on date."""
        soup = BeautifulSoup(self.html_content, "html.parser")

        # Get the latest news block
        main_container = soup.select_one("div.H6jWj.commercial-branding")
        if main_container:
            # Find the relevant ...
            news_blocks = main_container.select("div.VxecQ[data-travel_media-desktop^='top_news_block']")
            if news_blocks:
                logging.debug(f"news_blocks HTML:\n{news_blocks}")
                for idx, news_block in enumerate(news_blocks, start=1):
                    # Selecting title
                    title_element = news_block.select_one("div.NS1jn > div.PtPn1")
                    if title_element:
                        title = title_element.text.strip()
                        logging.debug(f'Title found {title}')
                    else:
                        logging.warning(f"No title found in news block {idx}")
                        break

                    image_url = news_block.select_one("div.Q0hlD img.PNvWC")
                    if image_url:
                        image_url = image_url['src']
                        logging.debug(f'Image URL found {image_url}')
                        image_filename = self.retrieve_and_save_image(image_url)
                    else:
                        logging.warning(f"No image URL found in news block {idx}")
                        # Selecting URL
                    url_element = news_block.select_one("a.dnRo0")
                    if url_element:
                        self.url = url_element.get("href")
                        logging.debug(f'url found {self.url}')
                        self.fetch_html_content()
                    else:
                        logging.warning(f"No URL found in news block {idx}")
                        continue

                    # Selecting description
                    soup = BeautifulSoup(self.html_content, "html.parser")

                    description_block = soup.select_one("div.WSusQ.fontSize_0")
                    if description_block:
                        paragraphs = description_block.find_all("p")
                        if paragraphs:
                            description = "\n".join([p.text.strip() for p in paragraphs])
                            logging.debug(f'Description found:\n{description}')
                        else:
                            logging.warning(f"No <p> tags found in description in news block {idx}")
                            continue
                    else:
                        logging.warning(f"No description found in news block {idx}")
                        continue

                    # Extract publication date from schema if available (you may need to adjust this part)
                    description_block_data = soup.select_one("div.kqSy_")
                    if description_block_data:
                        logging.debug(f"description_block_data :\n{description_block_data}")
                        time_element = description_block_data.select_one("time[datetime]")
                        if time_element:
                            pub_date_str = time_element.get("datetime")
                            pub_date = datetime.fromisoformat(pub_date_str)
                            logging.info(f"Publication date found: {pub_date}")
                        else:
                            logging.warning(f"No time element found in description_block_data in news block {idx}")
                            pub_date = datetime.now(timezone.utc)
                    else:
                        logging.warning(f"No description_block_data in news block{idx}")

                    # Calculate days old
                    today = datetime.now(timezone.utc)
                    days_old = (today - pub_date).days

                    if days_old < news_age_limit_days:
                        if not self.check_news_for_being_published_before(url_element):
                            # Save the extracted information
                            self.extracted_info = {
                                "Title": title,
                                "Description": description,
                                "Publication Date": pub_date.strftime("%a, %d %b %Y %H:%M %z"),
                                "ImageFileName": image_filename,
                                "Guid": self.url
                            }
                            logging.info(f"HTML news '{title}' is recent and valid.\n here is extracted info {self.extracted_info}")
                            return True
                        else:
                            logging.warning(f"This news with URL '{url}' was published before.")
                            return False
                    else:
                        logging.warning(f"HTML news '{title}' is too old.")
                        return False

                logging.warning("No recent news found within the age limit.")
                return False
            else:
                logging.warning("No valid news blocks found inside main container.")
                return False
        else:
            logging.warning("No valid main container found in HTML.")
            return False
        
    def extract_information(self):
        """Extract and return the news information."""
        return self.extracted_info
    
    def clean_html_text(self, html_text):
        """Clean HTML text."""
        soup = BeautifulSoup(html_text, "html.parser")
        cleaned_text = ' '.join(soup.stripped_strings)
        return cleaned_text

    def retrieve_and_save_image(self, image_url):
        """Retrieve and save the image."""
        try:
            response = requests.get(image_url, timeout=60)
            if response.status_code != 200:
                logging.error(f"Failed to retrieve image from {image_url}. Status code: {response.status_code}")
                return None
            
            parsed_url = urlparse(image_url)
            image_extension = os.path.splitext(os.path.basename(parsed_url.path))[1]
            logging.debug(f'image extension {image_extension}')

            #CLUTCH BAD IDEA IT MIGHT ME .web extention
            # If the extension is not found or is empty, use a default extension like .jpg
            if not image_extension:
                image_extension = ".jpg"

            local_image_filename = f"image_temp{image_extension}"
            with open(local_image_filename, "wb") as image_file:
                image_file.write(response.content)

            logging.info(f"Image saved locally as {local_image_filename}")
            return local_image_filename
        except Exception as err:
            logging.error(f"Failed to retrieve image. {err}")
            return None

    def save_to_json(self, filename="last_news.json"):
        """Save extracted information to JSON."""
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(self.extracted_info, json_file, ensure_ascii=False, indent=2)
            logging.info(f"Extracted information saved to {filename}")

    def check_news_for_being_published_before(self, current_guid):
        """Check if the news was already published before."""
        try:
            if os.path.exists('last_news.json') and os.path.getsize('last_news.json') > 0:
                with open('last_news.json', 'r', encoding="utf8") as json_file:
                    news_data = json.load(json_file)

                guid_value = news_data.get('Guid', '')
                return guid_value == current_guid
            else:
                return False
        except FileNotFoundError:
            return False
        except json.JSONDecodeError as err:
            logging.error(f"JSON decoding error: {err}")
            return False
