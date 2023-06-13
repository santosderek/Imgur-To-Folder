import json
from logging import getLogger
from os.path import expanduser, realpath
from pathlib import Path

logger = getLogger(__name__)


class Configuration:

    _singleton_instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._singleton_instance:
            cls._singleton_instance = super(Configuration, cls).__new__(cls)
        return cls._singleton_instance

    def __init__(
        self,
        config_path: str,
        access_token: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        download_path: str = "~",
        overwrite: bool = False,
        max_favorites: int = 30
    ):
        """
        Configuration class.

        Parameters:
            config_path (str): Path to the configuration file.
            access_token (str): The access token for the API.
            client_id (str): The client ID for the API.
            client_secret (str): The client secret for the API.
            download_path (str): The path to download the images to.
            refresh_token (str): The refresh token for the API.
            overwrite (bool): If True, overwrite existing files.
            max_favorites (int): The maximum number of favorites to download.
        """
        self.config_path = realpath(expanduser(config_path))
        self.access_token = access_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.overwrite = overwrite
        self.max_favorites = max_favorites

        self.download_path = realpath(expanduser(download_path))

    def convert_config_to_dict(self, overwrite_download_path=False):
        """
        Convert the current configuration to a dictionary.

        Parameters:
            overwrite_download_path (bool): If True, overwrite the download path with the current value.
        """
        return {
            'access_token': self.access_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'download_path': self.download_path if overwrite_download_path else self.download_path,
            'refresh_token': self.refresh_token
        }

    def save(self, overwrite_download_path=False):
        """
        Save the current configuration to the config file.

        Parameters:
            overwrite_download_path (bool): If True, overwrite the download path with the current value.
        """
        logger.debug('Saving configuration')
        config_dict = self.convert_config_to_dict(overwrite_download_path)

        _path = Path(self.config_path)

        if not _path.parent.exists():
            logger.debug('Creating config directory')
            _path.parent.mkdir(parents=True, exist_ok=True)

        with _path.open('w') as current_file:
            json.dump(config_dict, current_file, sort_keys=True, indent=4)
