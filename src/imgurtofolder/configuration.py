import json
import logs
from os import mkdir
import os.path

from dataclasses import dataclass

log = logs.Log('configuration')

@dataclass
class Configuration:

    config_path: str
    access_token: str
    client_id: str
    client_secret: str
    download_path: str
    refresh_token: str
    overwrite: bool = False
    max_favorites: int = 30

    _singleton_instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._singleton_instance:
            cls._singleton_instance = super(Configuration, cls).__new__(cls, *args, **kwargs)
        return cls._singleton_instance

    def __post_init__(self):
        self.download_path = os.path.realpath(os.path.expanduser(self.download_path))

    def set_access_token(self, token):
        log.debug('Setting access_token')
        self._access_token = token
        self.save_configuration()

    def set_client_id(self, client_id):
        log.debug('Setting client_id')
        self._client_id = client_id
        self.save_configuration()

    def set_client_secret(self, client_secret):
        log.debug('Setting client_secret')
        self._client_secret = client_secret
        self.save_configuration()

    def set_download_path(self, path):
        log.debug('Setting download_path')
        self.download_path = os.path.realpath(os.path.expanduser(path))

    def set_default_download_path(self, path):
        log.debug('Setting download_path')
        self.download_path = os.path.realpath(os.path.expanduser(path))
        self.save_configuration(True)

    def set_refresh_token(self, token):
        log.debug('Setting refresh token')
        self._refresh_token = token
        self.save_configuration()

    def convert_config_to_dict(self, overwrite_download_path=False):
        log.debug('Converting configuration to json')
        current_config = {}
        current_config['access_token'] = self._access_token
        current_config['client_id'] = self._client_id
        current_config['client_secret'] = self._client_secret
        if overwrite_download_path:
            current_config['download_path'] = self.download_path
        elif self.get_download_path():
            current_config['download_path'] = self.get_download_path()
        current_config['refresh_token'] = self._refresh_token
        return current_config

    def save_configuration(self, overwrite_download_path=False):
        log.debug('Saving configuration')
        config_dict = self.convert_config_to_dict(overwrite_download_path)

        if self._config_path[-len('.json'):]:
            folder_path = self._config_path[:self._config_path.rfind('/')]
        else:
            folder_path = self._config_path

        if not os.path.exists(folder_path):
            log.debug('Creating config directory')
            os.makedirs(folder_path)

        with open(self._config_path, 'w') as current_file:
            json.dump(config_dict, current_file, sort_keys=True, indent=4)
