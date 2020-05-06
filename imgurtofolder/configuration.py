import json
import logs
from os import mkdir
import os.path

log = logs.Log('configuration')

class Configuration:
    def __init__(self, config_path, access_token='', client_id='',
            client_secret='', download_path='', refresh_token='',
            overwrite=False):
        log.debug('Setting configuration')
        self._config_path   = config_path
        self._access_token  = access_token
        self._client_id     = client_id
        self._client_secret = client_secret
        self._download_path = os.path.realpath(os.path.expanduser(download_path))
        self._refresh_token = refresh_token
        self._overwrite     = overwrite
        log.debug('Configuration set')

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
        self._download_path = os.path.realpath(os.path.expanduser(path))

    def set_default_download_path(self, path):
        log.debug('Setting download_path')
        self._download_path = os.path.realpath(os.path.expanduser(path))
        self.save_configuration(True)

    def set_refresh_token(self, token):
        log.debug('Setting refresh token')
        self._refresh_token = token
        self.save_configuration()

    def get_access_token(self):
        return self._access_token

    def get_client_id(self):
        return self._client_id

    def get_client_secret(self):
        return self._client_secret

    def get_download_path(self):
        return self._download_path

    def get_refresh_token(self):
        return self._refresh_token

    def get_overwrite(self):
        return self._overwrite

    def convert_config_to_dict(self, overwrite_download_path=False):
        log.debug('Converting configuration to json')
        current_config = {}
        current_config['access_token'] = self._access_token
        current_config['client_id'] = self._client_id
        current_config['client_secret'] = self._client_secret
        if overwrite_download_path:
            current_config['download_path'] = self._download_path
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
