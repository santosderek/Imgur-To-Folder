import os
import re
import webbrowser
from copy import deepcopy
from dataclasses import dataclass
from pprint import pformat
from time import sleep
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from requests.exceptions import HTTPError

from imgurtofolder.api import ImgurAPI, Oauth
from imgurtofolder.configuration import Configuration
from imgurtofolder.logs import Log

log = Log('imgur')


class Imgur:
    def __init__(self, configuration):
        log.debug('Configuration set')
        self._configuration = configuration
        self._api = ImgurAPI(configuration)

    def get_account_images(self, username, page=0):
        """
        Get all images from an account

        Parameters:
            username (str): The username of the account
            page (int): The page number to start on

        Returns:
            list: A list of all images from the account
        """

        _next_page = lambda _username, _page: self._api.get(
            f'account/{_username}/images/{_page}',
            {
                'Authorization': 'Bearer %s' % self._configuration.access_token,
            }
        )

        account_images = []

        while len(response := _next_page(username, page)) != 0:
            log.info(f'Getting page {page} of account images')
            for item in response:
                account_images.append(item)
            response = _next_page(username, page)
            page += 1

        return account_images

    def get_gallery_favorites(self, username, sort='newest'):
        """
        Get all gallery favorites from an account

        Parameters:
            username (str): The username of the account
            sort (str): The sort order of the gallery favorites

        Returns:
            list: A list of all gallery favorites from the account
        """
        return self._api.get(
            f'account/{username}/gallery_favorites/{sort}',
            {
                'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
            }
        )

    def get_account_favorites(self, username, sort='newest', page=0, max_items=-1):
        """
        Get all favorites from an account

        Parameters:
            username (str): The username of the account
            sort (str): The sort order of the favorites
            page (int): The page number to start on
            max_items (int): The maximum number of items to return

        Returns:
            list: A list of all favorites from the account
        """

        _get_next_page = lambda _username, _page, _sort: self._api.get(
            f'account/{_username}/favorites/{_page}/{_sort}',
            {
                'Authorization': 'Bearer {self._configuration.access_token}',
            }
        )

        favorites = []

        while len(response := _get_next_page(username, page, sort)) != 0:
            if (max_items >= 0) and (len(favorites) > max_items):
                return favorites[:max_items]

            log.info(f'Getting page {page} of favorites')
            for item in response:
                favorites.append(item)
            page += 1

        return favorites

    def get_account_submissions(self, username):
        """
        Get all submissions from an account

        Parameters:
            username (str): The username of the account

        Returns:
            list: A list of all submissions from the account
        """
        return self._api.get(
            f'account/{username}/submissions/',
            {
                'Authorization': 'Client-ID %s' % self._configuration.client_id,
            }
        )
