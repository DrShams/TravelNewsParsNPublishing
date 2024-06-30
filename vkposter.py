import logging

import requests

from configurator import Configurator


class VKPoster:
    """ Class for posting data to the wall VK social media -> REST"""

    def __init__(self, config_file='config.conf'):
        """Initializes a VKPoster object. :param config_file: The path to the configuration file. """
        self.config = Configurator(config_file=config_file)

    def post_to_vk_wall(self, extracted_info):
        """Posts content to VK wall."""
        url = "https://api.vk.com/method/wall.post"
        #:param from_group: Specifies whether the post should be from a group.
        from_group = 1

        # Extract title and description from extracted_info
        title = extracted_info.get('Title', '')
        description = extracted_info.get('Description', '')
        filename = extracted_info.get('ImageFileName', '')
        # Combine title and description with a newline
        message = f"{title}\n\n{description}"

        if filename is not None:

            access_token = self.config.get_vk_settings()['access_token']
            version_vk = self.config.get_vk_settings()['vk_version']
            vk_owner_id = self.config.get_vk_settings()['vk_owner_id']
            user_albumid = self.config.get_vk_settings()['user_albumid']
            myuser_id = self.config.get_vk_settings()['myuser_id']

            photo_id = self.upload_photo_to_vk(access_token, user_albumid, filename, version_vk)
            photo = "photo" + myuser_id + "_" + str(photo_id)

            response = requests.post(
                url=url,
                params={
                    'access_token': access_token,
                    'from_group': from_group,
                    'owner_id': vk_owner_id,
                    'attachments': photo,
                    'v': version_vk
                },
                data={
                    'message': message
                },
                timeout=60
            )
        else:#do not attach photo
            response = requests.post(
                url=url,
                params={
                    'access_token': access_token,
                    'from_group': from_group,
                    'owner_id': vk_owner_id,
                    'v': version_vk
                },
                data={
                    'message': message
                },
                timeout=60
            )

        response_json = response.json()
        try:
            if 'error' in response_json and 'error_code' in response_json['error']:
                logging.debug(response_json)
                error_code = response_json['error']['error_code']

                if error_code == 15:
                    logging.error("Access denied. No access to call wall.post method.")
                else:
                    logging.error(f"Unexpected error with error code {error_code}")
            else:
                logging.info(f"Content successfully posted to vk wall with title {title}")
            
        except Exception as err:
            logging.error("Error parsing JSON:", err)

    def upload_photo_to_vk(self, access_token, album_id, photo_path, version):
        """Returns id photo after uploading image to the server"""
        upload_url = self.get_upload_url(access_token, album_id, version)

        with open(photo_path, 'rb') as file:
            photo_data = {'file1': file}

            upload_response = requests.post(upload_url, files=photo_data, timeout=60).json()
            logging.debug("upload_response " + str(upload_response))

        save_url = 'https://api.vk.com/method/photos.save'
        save_params = {
            'access_token': access_token,
            'album_id': upload_response['aid'],
            'server': upload_response['server'],
            'photos_list': upload_response['photos_list'],
            'hash': upload_response['hash'],
            'v': version,
        }

        save_response = requests.post(save_url, params=save_params, timeout=60).json()
        logging.debug("Save_response " + str(save_response))

        photo_id = save_response['response'][0]['id']
        logging.info(f"Photo was uploaded to the vk server's host and has an id {photo_id}")
        return photo_id

    def get_upload_url(self, access_token, album_id, version):
        """
        Retrieves the URL for uploading images.

        :param album_id: ID of the VK album.
        :param version: VK API version.
        :return: URL for uploading photos.
        """
        url = 'https://api.vk.com/method/photos.getUploadServer'
        params = {
            'access_token': access_token,
            'album_id': album_id,
            'v': version
        }

        response = requests.get(url, params=params, timeout=60).json()
        url_server = response['response']['upload_url']
        logging.info(f"Url for uploading photos was recieved {url_server}")
        return url_server
