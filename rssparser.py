import os
import logging
import json
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


class RSSParser:
    """Class for parsing an RSS feed."""

    def __init__(self, rss_url):
        """Initialize the RSSParser."""
        self.url = rss_url
        self.latest_item = None
        self.latest_pub_date = None
        self.extracted_info = {}
        self.xml_content = None  # Move the definition here

    def fetch_rss_content(self):
        """Fetch the RSS content."""
        try:
            response = requests.get(self.url, timeout=60)
            response.raise_for_status()  # Raise HTTPError for bad responses
            self.xml_content = response.content.decode('utf-8')
            logging.info("RSS content was successfully fetched")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching RSS content: {e}")
            raise  # Re-raise the exception to indicate fetch failure

        self.xml_content = response.content
        logging.info("Content RSS was recieves")

    def parse_rss_news(self, news_age_limit_days):
        """
        [1]Parse the RSS content.
        [2]Compare published date with current date and if that date less that value from config return that this news is valid
        [3]Open last_news.json file, compare links guid, and if that news already was published before
        """
        if not self.xml_content:
            logging.error("RSS content is empty or not fetched")
            return False

        try:
            root = ET.fromstring(self.xml_content)
        except ET.ParseError as e:
            logging.error(f"Error parsing RSS content: {e}")
            return False

        # Initialize variables to store parsed data
        parsed_date = None
        guid = None

        #Retrieve only last element
        for item in root.findall(".//item"):
            pub_date = item.find("pubDate").text
            guid = item.find("guid").text
            # Parse the date string
            try:
                parsed_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M %z")
            except ValueError as e:
                logging.error(f"Error parsing publication date: {e}")
                continue

            # Calculate the difference between today's date and the parsed date
            today = datetime.now(timezone.utc)
            difference = today - parsed_date
            days = difference.days

            self.latest_item = item
            self.latest_pub_date = pub_date
            break  # Exit loop after retrieving first news item

        logging.info(f"Last news with {parsed_date} was recieved this news was publicated {days} days ago")
        if days < news_age_limit_days:
            if self.check_news_for_being_pulished_before(guid) is False:
                return True
            else:
                logging.warning(f"This news with guid {guid} was published before")
                return False
        else:
            return False

    def clean_html_text(self, html_text):
        """Clean HTML text."""
        soup = BeautifulSoup(html_text, "html.parser")
        cleaned_text = ' '.join(soup.stripped_strings)
        return cleaned_text

    def extract_information(self):
        """Extract information from the latest news item."""
        if self.latest_item is not None:
            title = self.latest_item.find("title").text
            link = self.latest_item.find("link").text
            description_html = self.latest_item.find(".//description").text
            guid = self.latest_item.find("guid").text

            # Clean HTML tags and extra spaces
            description = self.clean_html_text(description_html)

            filename = self.retrieve_and_save_image(link)
            self.extracted_info = {
                "Title": title,
                "Description": description,
                "Publication Date": self.latest_pub_date,
                "ImageFileName": filename,
                "Guid": guid
            }
            logging.debug(self.extracted_info)
            logging.info("Information was successefully extracted from HTML")
            return self.extracted_info
        else:
            logging.error("No matching news item found.")
            return None

    def retrieve_and_save_image(self, link):
        """Retrieve and save the image."""
        response = requests.get(link, timeout=60)
        html_content = response.content

        soup = BeautifulSoup(html_content, "html.parser")
        try:
            # Extract the image using the provided XPath
            image = soup.select_one("html > body > main > div:nth-of-type(3) > div > article > div > img")
            image_url = image.get("src")
            self.extracted_info["Image URL"] = image_url

            # Download the image
            image_response = requests.get(image_url, timeout = 60)

            # Extract the file extension from the image URL
            parsed_url = urlparse(image_url)
            image_extension = os.path.splitext(os.path.basename(parsed_url.path))[1]

            # Save the image locally using the original file extension
            local_image_filename = f"image_temp{image_extension}"
            with open(local_image_filename, "wb") as image_file:
                image_file.write(image_response.content)

            logging.info(f"Image saved locally as {local_image_filename}")
            return local_image_filename
        except Exception as err:
            logging.error(f"No image found on the page. {err}")
            return None

    def save_to_json(self, filename="last_news.json"):
        """Save extracted information to JSON."""
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(self.extracted_info, json_file, ensure_ascii=False, indent=2)
            logging.info(f"Extracted information saved to {filename}")

    def check_news_for_being_pulished_before(self, current_guid):
        """If That news was already published before do not publish again"""
        with open('last_news.json', 'r', encoding="utf8") as json_file:
            news_data = json.load(json_file)

        # Retrieve the value associated with the "Guid" key
        guid_value = news_data.get('Guid', '')

        # Save the value to the 'guid' parameter
        guid = guid_value
        return guid == current_guid
