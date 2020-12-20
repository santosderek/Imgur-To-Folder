from .logs import Log
from .flask import create_application
from pprint import pformat
import re
import requests
import webbrowser


class Imgur:

    _log = Log('imgur')

    def __init__(self, configuration):
        self._log.debug('Configuration set')
        self._configuration = configuration

    def set_configuration(self, configuration):
        """Replace existing configuration with passed Configuration class."""
        self._log.debug('Changed configuration')
        self._configuration = configuration

    def authorize(self):
        """Prompt user to authenticate their application with Imgur"""
        url = "https://api.imgur.com/oauth2/authorize?client_id={client_id}&response_type=token&state=authenticated"
        url = url.format(
            client_id=self._configuration.get_client_id()
        )

        warning_banner = """
        This gives ImgurToFolder permission to view account information.
        ImgurToFolder does NOT collect any passwords or personal info!
        Everything is done though OAuth 2 APIs. All ITF code is open source in repo.
        """

        # Have user authorize their own app
        webbrowser.open_new(url)
        self._log.info("If a webpage did not load please go to: %s" % url)
        self._log.info(warning_banner)
        

        # Have user paste their own repsonse url
        self._log.info("---")
        self._log.info("After you loged in, you'll see the Imgur homepage.")
        self._log.info("Login to the application to authenticate.")
        # self._log.info("CTRL + C to stop flask server.")


        # flask_app = create_application() 
        # flask_app.run(host="127.0.0.1", port="8080") 

        user_input = str(input("Paste the redirected url here: "))

        # Save access_token and refresh_token to users config
        access_token = re.search(r'access_token=(\w+)', user_input).group(1)
        refresh_token = re.search(r'refresh_token=(\w+)', user_input).group(1)
        self._configuration.set_access_token(access_token)
        self._configuration.set_refresh_token(refresh_token)
        self._configuration.save_configuration()
        self._log.debug('Configuration saved')
        self._log.info('The application is now authorized')

    def generate_access_token(self):
        """Generates a new access token to be used throughout the application"""
        url = 'https://api.imgur.com/oauth2/token'
        data = {'refresh_token': self._configuration.get_refresh_token(),
                'client_id': self._configuration.get_client_id(),
                'client_secret': self._configuration.get_client_secret(),
                'grant_type': 'refresh_token'}
        headers = {
            'Authorization': 'Bearer %s' % self._configuration.get_access_token()
        }
        response = requests.request('POST',
                                    url,
                                    headers=headers,
                                    data=data,
                                    allow_redirects=False)
        response_json = response.json()

        self._configuration.set_access_token(response_json['access_token'])

    def get_account_images(self, username, page=0):
        """Returns a list of images found on the user's account"""
        url = f'https://api.imgur.com/3/account/{username}/images'
        headers = {
            'Authorization': 'Bearer {}'.format(self._configuration.get_access_token())
        }

        response = requests.request(
            "GET",
            url,
            headers=headers).json()

        if response['success'] is False:
            raise ImgurResponseNotSuccess(
                "Imgur Response: Error: {}".format(response['data']['error']))

        return response['data']

    def get_gallery_favorites(self, username, sort='newest', page=0):
        """Return a list of images the user has favorited"""
        url = f'https://api.imgur.com/3/account/{username}/gallery_favorites/{page}/{sort}'
        headers = {
            'Authorization': 'Bearer {}'.format(self._configuration.get_access_token())
        }

        response = requests.request(
            "GET",
            url,
            headers=headers).json()

        if response['success'] is False:
            raise ImgurResponseNotSuccess(
                "Imgur Response: Error: {}".format(response['data']['error']))

        return response['data']

    def get_account_favorites(self, username, sort='newest', page=0, max_items=80):
        """Returns a list of account favorites up to the max_items"""
        total_images = []

        while len(total_images) < max_items:
            url = f"https://api.imgur.com/3/account/{username}/favorites/{page}/{sort}"
            headers = {
                'Authorization': 'Bearer {}'.format(self._configuration.get_access_token())
            }
            response = requests.request(
                "GET",
                url,
                headers=headers).json()

            if 'errors' in response and response['errors'][0]['status'] == 'Unauthorized':
                raise UnauthorizedError(
                    "You have not authorized the application.")

            if 'success' in response and response['success'] is False:
                raise ImgurResponseNotSuccess(
                    "Imgur Response: Error: {}".format(response['data']['error']))

            for image in response['data']:
                if 'data' in response and len(total_images) < max_items:
                    total_images.append(image)

        return total_images

    def get_account_submissions(self, username):
        """Returns a list of account submissions by username"""
        url = f'https://api.imgur.com/3/account/{username}/submissions/'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers=headers).json()

        if response['success'] is False:
            raise ImgurResponseNotSuccess(
                "Imgur Response: Error: {}".format(response['data']['error']))

        return response['data']

    def get_album(self, album_hash):
        """Returns the albumn metadata"""
        url = f'https://api.imgur.com/3/album/{album_hash}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers=headers).json()

        if response['success'] is False:
            raise ImgurResponseNotSuccess(
                "Imgur Response: Error: {}".format(response['data']['error']))

        return response['data']

    def get_gallery_album(self, gallery_hash):
        """Returns a gallery metadata"""
        url = f'https://api.imgur.com/3/gallery/{gallery_hash}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers=headers).json()

        if response['success'] is False:
            raise ImgurResponseNotSuccess(
                "Imgur Response: Error: {}".format(response['data']['error']))

        return response['data']

    def get_subreddit_gallery(self, subreddit, sort='time', window='day', page=0):
        """Returns a subreddit gallery metadata"""
        url = f'https://api.imgur.com/3/gallery/r/{subreddit}/{sort}/{window}/{page}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers=headers).json()

        if response['success'] is False:
            raise ImgurResponseNotSuccess(
                "Imgur Response: Error: {}".format(response['data']['error']))

        return response['data']

    def get_subreddit_image(self, subreddit, image_id):
        """Returns a subreddit image metadata"""
        url = f'https://api.imgur.com/3/gallery/r/{subreddit}/{image_id}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        response = requests.request('GET', url, headers=headers).json()

        if response['success'] is False:
            raise ImgurResponseNotSuccess(
                "Imgur Response: Error: {}".format(response['data']['error']))

        return response['data']

    def get_tag(self, tag, sort='top', window='week', page=0, max_items=30):
        """Returns all images up to the max_items from a tag"""
        total_images = []

        while len(total_images) < max_items:
            url = f'https://api.imgur.com/3/gallery/t/{tag}/{sort}/{window}/{page}'
            headers = {
                'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
            }
            response = requests.request('GET', url, headers=headers).json()

            if response['success'] is False:
                break

            for image in response['data']:
                if 'data' in response and len(total_images) < max_items:
                    total_images.append(image)

        return total_images


class Image():
    def __init__(self, dictionary):
        self.__dict__.update(dictionary)


class Album():
    def __init__(self, dictionary):
        self.__dict__.update(dictionary)


class UnauthorizedError(Exception):
    pass


class ImgurResponseNotSuccess(Exception):
    pass
