from .logs import Log
import json
import os.path


class Configuration:
    _log = Log('configuration')

    def __init__(self, config_path, access_token='', client_id='',
                 client_secret='', download_path='', refresh_token='',
                 overwrite=False):
        self._log.debug('Setting configuration')
        self._config_path = config_path
        self._access_token = access_token
        self._client_id = client_id
        self._client_secret = client_secret
        download_host_path = os.path.expanduser(download_path)
        self._download_path = os.path.realpath(download_host_path)
        self._refresh_token = refresh_token
        self._overwrite = overwrite
        self._log.debug('Configuration set')

    def set_access_token(self, token):
        self._log.debug('Setting access_token')
        self._access_token = token
        self.save_configuration()

    def set_client_id(self, client_id):
        self._log.debug('Setting client_id')
        self._client_id = client_id
        self.save_configuration()

    def set_client_secret(self, client_secret):
        self._log.debug('Setting client_secret')
        self._client_secret = client_secret
        self.save_configuration()

    def set_download_path(self, path):
        self._log.debug('Setting download_path')
        self._download_path = os.path.realpath(os.path.expanduser(path))

    def set_default_download_path(self, path):
        self._log.debug('Setting download_path')
        self._download_path = os.path.realpath(os.path.expanduser(path))
        self.save_configuration(True)

    def set_refresh_token(self, token):
        self._log.debug('Setting refresh token')
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
        self._log.debug('Converting configuration to json')
        current_config = dict(
            access_token=self._access_token,
            client_id=self._client_id,
            client_secret=self._client_secret,
            download_path=self._download_path if overwrite_download_path else self.get_download_path(),
            refresh_token=self._refresh_token,
            overwrite=self._overwrite
        )
        return current_config

    def save_configuration(self, overwrite_download_path=False):
        self._log.debug('Saving configuration')
        config_dict = self.convert_config_to_dict(overwrite_download_path)

        if self._config_path[-len('.json'):]:
            folder_path = self._config_path[:self._config_path.rfind('/')]
        else:
            folder_path = self._config_path

        if not os.path.exists(folder_path):
            self._log.debug('Creating config directory')
            os.makedirs(folder_path)

        with open(self._config_path, 'w') as current_file:
            json.dump(config_dict, current_file, sort_keys=True, indent=4)
