import yaml
import logging

class Configurator:
    def __init__(self, config_file='config.yaml'):
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)

    def debug_config(self):
        for section, values in self.config.items():
            logging.debug(f"Section: {section}")
            for key, value in values.items():
                logging.debug(f" {key} = {value}")

    def get_logging_level(self):
        return self.config.get('Logging', {}).get('level', 'DEBUG')

    def get_file_path(self):
        return self.config.get('Logging', {}).get('file_path', 'console.log')

    def get_date_format(self):
        return self.config.get('Logging', {}).get('date_format')

    def get_news_age_limit_days(self):
        return int(self.config.get('NewsSettings', {}).get('news_age_limit_days', 0))

    def get_vk_settings(self):
        return self.config.get('VKSettings', {})

    def get_sources(self):
        sources = {}
        if 'Sources' in self.config:
            for name, details in self.config['Sources'].items():
                url = details.get('url', '')
                endpoints = details.get('endpoints', [])
                sources[name] = {'url': url, 'endpoints': endpoints}
        else:
            logging.error("No sources found in the config file")
        return sources
    
    def get_section_links(self, section_name):
        """Get the endpoints for the given section"""
        sources = self.get_sources()
        if section_name in sources:
            return sources[section_name]['endpoints']
        else:
            logging.error(f"Section {section_name} not found in the config file")
            return []