import re
import webbrowser
from copy import deepcopy
from logging import getLogger
from pprint import pformat
from typing import Dict, Optional
from urllib.parse import urljoin

import requests
from requests.exceptions import HTTPError

from imgurtofolder.configuration import Configuration

logger = getLogger(__name__)


class OAuth:

    def __init__(self, configuration: Configuration):
        self._configuration = configuration

    def authorize(self):
        """
        Authorize the application to access the users account

        Raises:
            ValueError: If the user does not provide the correct input
        """
        url = (
            'https://api.imgur.com/oauth2/authorize?'
            'response_type=token'
            f'&client_id={self._configuration.client_id}'
        )

        # Have user authorize their own app
        webbrowser.open_new(url)
        logger.info("If a webpage did not load please go to: %s" % url)
        logger.info("This gives ImgurToFolder permission to view account information.")
        logger.info("ImgurToFolder does NOT collect any passwords or personal info!")

        # Have user paste their own repsonse url
        logger.info("---")
        logger.info("After you loged in, you'll see the Imgur homepage.")
        user_input = str(input("Paste the redirected url here: "))

        # Save access_token and refresh_token to users config
        search: Optional[re.Match] = re.search(r'access_token=(\w+)', user_input)
        if not search:
            raise ValueError('Could not find access_token in user input')
        self._configuration.access_token = search.group(1)

        search: Optional[re.Match] = re.search(r'refresh_token=(\w+)', user_input)
        if not search:
            raise ValueError('Could not find refresh_token in user input')
        self._configuration.refresh_token = search.group(1)

        self._configuration.save()
        logger.debug('Configuration saved')
        logger.info('The application is now authorized')

    def generate_access_token(self):
        url = 'https://api.imgur.com/oauth2/token'

        response = requests.request('POST',
                                    url,
                                    headers=headers,
                                    data={
                                        'refresh_token': self._configuration.refresh_token,
                                        'client_id': self._configuration.client_id,
                                        'client_secret': self._configuration.client_secret,
                                        'grant_type': 'refresh_token'
                                    },
                                    allow_redirects=False)
        response_json = response.json()

        self._configuration.access_token = response_json['access_token']


def _raise_exception_given_response(response: requests.Response):
    message = f'Request returned incorrect response: {response.status_code} - {response}'
    logger.error(message)
    logger.debug(pformat(response.json()))
    raise HTTPError(message)


class ImgurAPI:
    """
    A class to interact with the Imgur API as a singleton
    """

    DEFAULT_HEADERS: Dict[str, str] = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    BASE_URL = 'https://api.imgur.com'
    API_PREFIX = '/3/'

    _singleton_instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._singleton_instance:
            cls._singleton_instance = super().__new__(cls)
        return cls._singleton_instance

    def __init__(self, configuration: Configuration):
        self._configuration = configuration
        self._oauth = OAuth(configuration)
        self.base_url = urljoin(self.BASE_URL, self.API_PREFIX)

    def _make_request(
            self,
            method: str,
            url: str,
            headers: Optional[Dict[str, str]] = None,
            return_raw_response: bool = False,
            **kwargs
    ):
        """
        Make a request to the Imgur API

        Parameters:
            method (str): The HTTP method to use
            url (str): The url to make the request to
            headers (dict): The headers to send with the request
            return_raw_response (bool): Whether to return the raw response or the parsed json
            **kwargs: Any other arguments to pass to the requests library

        Returns:
            [dict | requests.Response]: The response from the API
        """

        _headers = deepcopy(self.DEFAULT_HEADERS)
        _headers.update(headers or {})

        response = requests.request(
            method,
            urljoin(self.base_url, url),
            headers=_headers,
            **kwargs
        )

        if return_raw_response:
            return response

        response.raise_for_status()

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            _raise_exception_given_response(response)

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs):
        """
        Make a GET request to the Imgur API

        Parameters:
            url (str): The url to make the request to
            headers (dict): The headers to send with the request
            **kwargs: Any other arguments to pass to the requests library

        Returns:
            [dict | requests.Response]: The response from the API
        """
        return self._make_request('GET', url, headers=headers, **kwargs)

    def post(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs):
        """
        Make a POST request to the Imgur API

        Parameters:
            url (str): The url to make the request to
            headers (dict): The headers to send with the request
            **kwargs: Any other arguments to pass to the requests library

        Returns:
            [dict | requests.Response]: The response from the API
        """
        return self._make_request('POST', url, headers=headers, **kwargs)

    def delete(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs):
        """
        Make a DELETE request to the Imgur API

        Parameters:
            url (str): The url to make the request to
            headers (dict): The headers to send with the request
            **kwargs: Any other arguments to pass to the requests library

        Returns:
            [dict | requests.Response]: The response from the API
        """
        return self._make_request('DELETE', url, headers=headers, **kwargs)

    def put(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs):
        """
        Make a PUT request to the Imgur API

        Parameters:
            url (str): The url to make the request to
            headers (dict): The headers to send with the request
            **kwargs: Any other arguments to pass to the requests library

        Returns:
            [dict | requests.Response]: The response from the API
        """
        return self._make_request('PUT', url, headers=headers, **kwargs)
