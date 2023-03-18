# Derek Santos
import json
import os
import re
import shutil
from os.path import basename
from pprint import pformat
from time import sleep
from urllib.parse import urlparse

import logs
import requests
from imgur import Imgur

from imgurtofolder.objects import Album, Gallery, Image, Subreddit

log = logs.Log('downloader')


def mkdir(path):
    log.debug("Checking if folder exists")
    if not os.path.exists(path):
        log.debug("Creating folder: %s" % path)
        os.makedirs(path)


def replace_characters(word):
    # NOTE: '\\/:*?"<>|.' are invalid folder characters in a file system
    invalid_characters = ['\\', "'", '/', ':',
                          '*', '?', '"', '<',
                          '>', '|', '.', '\n']

    for character in invalid_characters:
        word = word.replace(character, '')

    return word.strip()


class Imgur_Downloader:

    def __init__(self, configuration):
        self._configuration = configuration

    def parse_id(self, url, page=0, sort='time', window='day'):
        """
        Parses the url and downloads the image or album

        Parameters:
            url (str): The url to parse
            page (int): The page to start on
            max_items (int): The maximum number of items to download
            sort (str): The sort type
            window (str): The window type
        """
        imgur_base_extensions = {
            'album': [r'(/a/)(\w+)'],
            'gallery': [r'(/g/)(\w+)', r'(/gallery/)(\w+)'],
            'subreddit': [r'(/r/)(\w+)\/(\w+)', r'(/r/)(\w+)$'],
            'tag': [r'(/t/)(\w+)']
        }

        if any(re.search(item, url) for item in imgur_base_extensions['album']):
            for item in imgur_base_extensions['album']:
                result = re.search(item, url).group(
                    2) if re.search(item, url) else None
                if result:
                    Album(url).download(result)

        elif any(re.search(item, url) for item in imgur_base_extensions['gallery']):
            for item in imgur_base_extensions['gallery']:
                result = re.search(item, url).group(
                    2) if re.search(item, url) else None
                if result:
                    Gallery(url,).download(result)

        elif any(re.search(item, url) for item in imgur_base_extensions['subreddit']):
            for item in imgur_base_extensions['subreddit']:
                if re.search(item, url) is None:
                    continue

                subreddit = re.search(item, url).group(2)
                id = re.search(item, url).group(
                    3) if re.compile(item).groups > 2 else None

                if id is None and subreddit is not None:
                    Subreddit(url).download(
                        subreddit,
                        sort=sort,
                        window=window,
                        page=page,
                        max_items=self._configuration.max_items
                    )

                elif subreddit is not None and id is not None:
                    Subreddit(url).download_subreddit_gallery(subreddit, id)

        elif any(re.search(item, url) for item in imgur_base_extensions['tag']):
            for item in imgur_base_extensions['tag']:
                result = re.search(item, url).group(
                    2) if re.search(item, url) else None
                if result:
                    Tag(url).download(
                        result,
                        page=page,
                        max_items=self._configuration.max_items
                    )

        else:
            log.info(f'Downloading image: {basename(urlparse(url).path)}')
            Image(url, basename(urlparse(url).path)).download(
                self.get_download_path()
            )

    def download_account_images(self, username, page=0, max_items=None):
        account_images = self.get_account_images(username, page=page)

        if max_items:
            account_images = account_images[:max_items]

        for image in account_images:
            self.parse_id(image['link'])
