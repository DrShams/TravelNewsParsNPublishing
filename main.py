#!/usr/bin/python3
import os
import logging
import random
import sys

from rssparser import RSSParser
from vkposter import VKPoster
from configurator import Configurator
from htmlparser import HTMLParser

class Main:
    def __init__(self, config_file='config.conf'):
        """Read Config File"""
        self.config = Configurator(config_file=config_file)

        # Configure logging
        self.configure_logging()

        #Если новости из основного раздела(по тем странам по которым летаем) будут исчерпаны, перейти к другому разделу
        self.section_to_parse_news = "TravelLinks"
        self.travel_links_section = self.config.get_section_links(self.section_to_parse_news)

        random_travel_link = self.get_random_link(self.section_to_parse_news, self.config)
        logging.info(f"Random {self.section_to_parse_news} Link: {random_travel_link}")

        self.rss_parser = RSSParser(random_travel_link)
        self.vk_poster = VKPoster()

        other_sources_links = self.config.get_section_links("OtherSourcesOfNews")
        logging.info(f"other_sources_links {other_sources_links}")
        other_source_url = other_sources_links.get("all")
        logging.info(f"other_source_url {other_source_url}")
        if not other_source_url:
            logging.error("No URL found in OtherSourcesOfNews section")
            sys.exit(1)

        self.html_parser = HTMLParser(other_source_url)  # Initialize HTMLParser with a valid URL

    def configure_logging(self):
        """Set up logging"""
        logging_level = self.config.get_logging_level()
        file_path = self.config.get_file_path()
        date_format = self.config.get_date_format()

        logging.basicConfig(
            level=logging.getLevelName(logging_level),
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt=date_format
        )

        # Create a file handler and set the logging level
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Create a formatter for the file handler
        file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt=date_format)
        file_handler.setFormatter(file_formatter)

        # Get the root logger and add the file handler
        logger = logging.getLogger()
        logger.addHandler(file_handler)

    def run(self):
        """Fetch and analyze news, then Post to VK"""
        is_news_recent = False
        attempt = 0
        news_age_limit_days = self.config.get_news_age_limit_days()#days
        while is_news_recent is False:
            attempt += 1
            self.rss_parser.fetch_rss_content()
            is_news_recent = self.rss_parser.parse_rss_news(news_age_limit_days)
            if is_news_recent:
                logging.info("News Approved")
            else:
                numlinks = len(self.travel_links_section)
                if attempt > numlinks:
                    if self.section_to_parse_news == "NewsLinks":
                        logging.warning("No news for today")
                        
                        # Try fetching from the new HTML source
                        self.html_parser.fetch_html_content()
                        is_news_recent = self.html_parser.parse_html_news(news_age_limit_days)
                        if not is_news_recent:
                            logging.warning("No news from the HTML source as well")
                            sys.exit(0)
                        else:
                            logging.info("News from HTML source approved")
                    else:
                        self.section_to_parse_news = "NewsLinks"
                        self.travel_links_section = self.config.get_section_links(self.section_to_parse_news)
                        numlinks = len(self.travel_links_section)
                        attempt = 1

                random_travel_link = self.get_random_link(self.section_to_parse_news, self.config)
                logging.info("Random Travel Link:" + str(random_travel_link))

                self.rss_parser = RSSParser(random_travel_link)
                logging.info(f"NEWS OLD attempt {attempt} / {numlinks}")


        #Save news to the file
        if is_news_recent:
            if self.rss_parser.latest_item:
                data = self.rss_parser.extract_information()
                self.rss_parser.save_to_json()
                filename = data['ImageFileName']                
            else:
                self.html_parser.extract_information()
                self.html_parser.save_to_json()
                filename = "image_temp.jpg"#CAREFUL EXTENTION MIGHT BE DIFFERENT!

            #Post news to vk
            #self.vk_poster.post_to_vk_wall(self.rss_parser.extracted_info   if self.rss_parser.latest_item else self.html_parser.extracted_info)
            try:
                os.remove(filename)
                logging.debug(f'successefully remove {filename}')
            except Exception as e:
                logging.error(f'Can"t delete this file {filename} because of \n{e}')

    def get_random_link(self, section_name, config):
        """Return random link from Config file for rss news"""
        section_links = self.config.get_section_links(section_name)
        return random.choice(list(section_links.values()))

if __name__ == "__main__":
    try:
        main = Main()
        main.run()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
