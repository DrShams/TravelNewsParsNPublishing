#!/usr/bin/python3
import os
import logging
import random
import sys

from rssparser import RSSParser
from vkposter import VKPoster
from configurator import Configurator, LoggerConfigurator
from urllib.parse import urljoin, urlparse, urlunparse

class Main:
    def __init__(self, config_file='config.yaml'):
        """Read Config File"""
        self.config = Configurator(config_file=config_file)

        # Configure logging
        LoggerConfigurator(self.config).configure()

        # Initialize RSSParser and VKPoster
        self.rss_parser = None
        self.vk_poster = VKPoster(config_file=config_file)

    def run(self):
        """Fetch and analyze news, then Post to VK"""
        is_news_recent = False
        attempt = 0
        news_age_limit_days = self.config.get_news_age_limit_days()

        while not is_news_recent:
            attempt += 1
            rss_url = self.get_random_rss_url()
            logging.info(f'rss_url {rss_url}')
            self.rss_parser = RSSParser(rss_url)

            try:
                self.rss_parser.fetch_rss_content()
                is_news_recent = self.rss_parser.parse_rss_news(news_age_limit_days)
            except Exception as e:
                logging.error(f"Error fetching or parsing RSS: {e}")
                continue

            if is_news_recent:
                logging.info("News Approved")
            else:
                logging.warning("No recent news found.")
                sources = self.config.get_sources()
                numlinks = len(sources.get('Votpusk', {}).get('endpoints', []))
                if attempt > numlinks:
                    logging.warning("No news for today")
                    break

        # Save news to the file
        if is_news_recent:
            if self.rss_parser.latest_item:
                data = self.rss_parser.extract_information()
                self.rss_parser.save_to_json()
                filename = data['ImageFileName']

            # Post news to VK
            self.vk_poster.post_to_vk_wall(self.rss_parser.extracted_info)
            try:
                os.remove(filename)
                logging.info(f'Successfully removed {filename}')
            except Exception as e:
                logging.error(f"Can't delete this file {filename} because of:\n{e}")

    def get_random_link(self, section_name):
        """Return random link from Config file for rss news"""
        section_links = self.config.get_section_links(section_name)
        return random.choice(section_links)
    
    def get_random_rss_url(self):
        """Return random RSS URL from Config file."""
        sources = self.config.get_sources()
        random_source_name = random.choice(list(sources.keys()))  # Choose a random source name
        random_source = sources[random_source_name]  # Get the source details
        random_endpoint = random.choice(random_source['endpoints'])  # Choose a random endpoint
        
        # Ensure the endpoint is concatenated correctly to the base URL
        base_url = random_source['url'].rstrip('/')  # Remove trailing slashes from base URL
        if random_endpoint.startswith('/'):
            random_endpoint = random_endpoint.lstrip('/')
        
        rss_url = f"{base_url}/{random_endpoint}"  # Construct the full URL
        return rss_url


if __name__ == "__main__":
    try:
        main = Main()
        main.run()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
