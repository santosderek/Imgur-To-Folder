import logs
from pprint import pformat
import re
import requests
import webbrowser
from time import sleep
import os

log = logs.Log('imgur')


class Imgur:
    def __init__(self, configuration):
        log.debug('Configuration set')
        self._configuration = configuration

    def set_configuration(self, configuration):
        log.debug('Changed configuration')
        self._configuration = configuration

    def set_download_path(self, path):
        log.debug('Chaning download path')
        if not os.path.exists(path):
            os.makedirs(path)
        self._configuration.set_download_path(path)

    def set_default_folder_path(self, path):
        log.debug('Chaning download path')
        if not os.path.exists(path):
            os.makedirs(path)
        self._configuration.set_default_download_path(path)

    def get_download_path(self):
        return self._configuration.get_download_path()

    def get_overwrite(self):
        return self._configuration.get_overwrite()

    def authorize(self):
        url  = 'https://api.imgur.com/oauth2/authorize?'
        url += 'response_type=token'
        url += '&client_id=%s' % self._configuration.get_client_id()

        # Have user authorize their own app
        webbrowser.open_new(url)
        log.info("If a webpage did not load please go to: %s" % url)
        log.info("This gives ImgurToFolder permission to view account information.")
        log.info("ImgurToFolder does NOT collect any passwords or personal info!")

        # Have user paste their own repsonse url
        log.info("---")
        log.info("After you loged in, you'll see the Imgur homepage.")
        user_input = str(input("Paste the redirected url here: "))

        # Save access_token and refresh_token to users config
        access_token = re.search('access_token=(\w+)', user_input).group(1)
        refresh_token = re.search('refresh_token=(\w+)', user_input).group(1)
        self._configuration.set_access_token(access_token)
        self._configuration.set_refresh_token(refresh_token)
        self._configuration.save_configuration()
        log.debug('Configuration saved')
        log.info('The application is now authorized')

    def generate_access_token(self):
        url = 'https://api.imgur.com/oauth2/token'
        data = {'refresh_token': self._configuration.get_refresh_token(),
                    'client_id': self._configuration.get_client_id(),
                    'client_secret': self._configuration.get_client_secret(),
                    'grant_type': 'refresh_token'}
        response = requests.request('POST',
                                    url,
                                    headers = headers,
                                    data = data,
                                    allow_redirects=False)
        response_json = response.json()

        # TODO: Make sure this works
        self._configuration.set_access_token(response_json['access_token'])

    def get_url_data(self, url, headers, data):
            response = requests.request('GET', url,  headers=headers, data=data)
            if response.status_code == 200 and not 'error' in response.json()['data']:
                return response.json()['data']
            else:
                message = (response.status_code, pformat(response.json()['data']))
                log.error(' '.join(message))
                raise Exception(message)

    def get_account_images(self, username, page=0):

        if not self._configuration.get_access_token():
            self.authorize()

        url = f'https://api.imgur.com/3/account/{username}/images/{page}'
        headers = {
            'Authorization': 'Bearer %s' % self._configuration.get_access_token()
        }
        account_images = []
        response = self.get_url_data(url, headers, None)

        while len(response) != 0:
            log.info('Getting page %d of account images' % page)
            for item in response:
                account_images.append(item)
            url = f'https://api.imgur.com/3/account/{username}/images/{page}'
            response = self.get_url_data(url, headers, None)
            page += 1

        return account_images

    def get_gallery_favorites(self, username, sort='newest'):
        url = f'https://api.imgur.com/3/account/{username}/gallery_favorites/{sort}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers = headers)
        return response.json()

    def get_account_favorites(self, username, sort='newest', page=0, max_items=-1):

        if not self._configuration.get_access_token():
            self.authorize()

        headers = {
            'Authorization': 'Bearer %s' % self._configuration.get_access_token()
        }
        url = f'https://api.imgur.com/3/account/{username}/favorites/{page}/{sort}'
        response = self.get_url_data(url, headers, None)
        favorites = []
        while len(response) != 0:
            if (max_items >= 0) and (len(favorites) > max_items):
                return favorites[:max_items]

            log.info('Getting page %d of favorites' % page)
            for item in response:
                favorites.append(item)
            url = f'https://api.imgur.com/3/account/{username}/favorites/{page}/{sort}'
            response = self.get_url_data(url, headers, None)
            page += 1

        return favorites

    def get_account_submissions(self, username):
        url = f'https://api.imgur.com/3/account/{username}/submissions/'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers = headers)
        return response.json()

    def get_album(self, album_hash):
        url = f'https://api.imgur.com/3/album/{album_hash}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers = headers)
        return response.json()

    def get_gallery_album(self, gallery_hash):
        url = f'https://api.imgur.com/3/gallery/{gallery_hash}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers = headers)
        return response.json()

    def get_subreddit_gallery(self, subreddit, sort='time', window='day', page=0):
        url = f'https://api.imgur.com/3/gallery/r/{subreddit}/{sort}/{window}/{page}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers = headers)
        return response.json()

    def get_subreddit_image(self, subreddit, image_id):
        url = f'https://api.imgur.com/3/gallery/r/{subreddit}/{image_id}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers = headers)
        return response.json()

    def get_tag(self, tag, sort='top', window='week', page=0, max_items=30):
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }

        items = []
        url = f'https://api.imgur.com/3/gallery/t/{tag}/{sort}/{window}/{page}'
        response = self.get_url_data(url, headers, None)

        while len(response) != 0 and len(items) < max_items:
            for item in response['items']:
                items.append(item)

            url = f'https://api.imgur.com/3/gallery/t/{tag}/{sort}/{window}/{page}'
            log.debug('Url to download: %s' % url)
            response = self.get_url_data(url, headers, None)
            page += 1
        return items[:max_items + 1]
