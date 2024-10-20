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
        
class LoggerConfigurator:
    def __init__(self, config):
        self.config = config

    def configure(self):
        """Set up logging"""
        logging_level = self.config.get_logging_level()
        file_path = self.config.get_file_path()
        date_format = self.config.get_date_format()

        print(f"Logging Level: {logging_level}, File Path: {file_path}, Date Format: {date_format}")  # Debug Line

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