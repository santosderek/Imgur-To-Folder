from abc import ABC, abstractmethod
from typing import Optional
from imgurtofolder.constants import IMGUR_BASE_EXTENSIONS
import os
from pathlib import Path
from pprint import pformat
from time import sleep
from typing import List

import requests
import re
from imgurtofolder.imgur import ImgurAPI

from logging import getLogger

from pprint import pformat
from os.path import exists
import shutil

import asyncio

logger = getLogger(__name__)


def replace_characters(word):
    # NOTE: '\\/:*?"<>|.' are invalid folder characters in a file system
    invalid_characters = ['\\', "'", '/', ':',
                          '*', '?', '"', '<',
                          '>', '|', '.', '\n']

    for character in invalid_characters:
        word = word.replace(character, '')

    return word.strip()


class Downloadable(ABC):
    """
    Abstract class which holds all the common methods for downloading images and albums.
    """

    def __init__(self, hash: str, api: ImgurAPI):
        self.hash = hash
        self.api = api

    @abstractmethod
    def get_metadata(self, **kwargs) -> 'Downloadable':
        """
        Gets the metadata for the object using the API.
        """
        ...

    @abstractmethod
    async def download(self, overwrite: bool = False, **kwargs) -> 'Downloadable':
        """
        Downloads the multi-media blob.
        """
        ...


class Image(Downloadable):
    """
    Class which holds all the methods for downloading images.
    """

    def get_metadata(self, **kwargs) -> dict:
        """
        Gets the metadata for the image using the API.

        Returns:
            dict: The metadata for the image
        """
        return self.api.get(
            url=f"image/{self.hash}",
            headers={
                "Authorization": f"Client-ID {self.api._configuration.client_id}",
            }
        ).get('data')

    async def download(self, path, overwrite: bool = False, enumeration: Optional[int] = None):
        """
        Downloads a file from a url to a path

        Parameters:
            path (str): The path to download the file to
            overwrite (bool): If True, overwrite existing files
            kwargs: Additional arguments

        Raises:
            ValueError: If the response code is not 200
        """

        metadata = self.get_metadata()

        _title = metadata.get('title') or metadata.get('id')
        suffix = Path(metadata.get('link')).suffix
        _filename = f"{_title}{(' - ' + str(enumeration)) if enumeration else ''}{suffix}"

        _url = metadata.get('link')

        _path = Path(path)

        if not _path.exists():
            logger.debug(f'Creating folder path {_path}')
            os.makedirs(path)

        _full_path = _path / _filename

        if not overwrite and _full_path.exists():
            logger.info(f'Skipping {_full_path} because it already exists')
            return

        response: requests.Response = self.api.get(_url, return_raw_response=True, stream=True)

        if response.status_code != 200:
            logger.error('Error downloading image: %s' % pformat(response.json()))
            raise ValueError(f'Error downloading image: {self.hash}')

        file_size = \
            int(response.headers.get('content-length', 0)) / float(1 << 20)

        logger.info('\t%s, File Size: %.2f MB' % (_full_path, file_size))

        # Placing a sleep here to prevent rate limiting
        await asyncio.sleep(.1)

        with _full_path.open('wb') as image_file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, image_file)


class Album(Downloadable):
    """
    Class which holds all the methods for downloading albums.
    """

    def get_metadata(self, **kwargs) -> dict:
        """
        Gets the metadata for the image using the API.

        Returns:
            dict: The metadata for the image
        """
        # TODO: Regex could be better
        # _hash = re.search(r"(https?)?(.*\.com\/)(\w+)(\..*)?$", self.url).group(3)

        return self.api.get(
            url=f"album/{self.hash}",
            headers={
                "Authorization": f"Client-ID {self.api._configuration.client_id}",
            }
        ).get('data')

    async def download(self, path: str = None, overwrite: bool = False):

        metadata = self.get_metadata()

        _title = replace_characters(metadata.get('title') or metadata.get('id'))
        _path = Path(self.api._configuration.download_path) / _title

        logger.debug("Checking if folder exists")
        _path.mkdir(parents=True, exist_ok=True)

        logger.info('Downloading album: %s' % _title)

        _images = metadata.get('images') or []

        for position, image in enumerate(_images, start=1):
            await asyncio.create_task(
                Image(
                    hash=image.get('id'),
                    api=self.api
                ).download(
                    path=_path,
                    overwrite=overwrite,
                    enumeration=position
                )
            )


class Gallery(Album):
    """
    Class which holds all the methods for downloading galleries.
    """

    def get_metadata(self, gallery_hash):
        url = f'gallery/{gallery_hash}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        return self._api.get(url, headers=headers)

    def download(self, id):

        logger.debug('Getting Gallery details')
        album = self.get_gallery_album(id)['data']
        title = album['title'] if album['title'] else album['id']
        title = self.replace_characters(title)
        path = os.path.join(self.get_download_path(), title)

        logger.debug("Checking if folder exists")
        if not os.path.exists(path):
            logger.debug("Creating folder: %s" % path)
            os.makedirs(path)

        if 'images' in album:
            logger.info('Downloading gallery %s' % album['id'])
            for position, image in enumerate(album['images'], start=1):
                image_link, filetype = self.get_image_link(image)
                filename = album['id'] + ' - ' + str(position) + filetype
                Image().download(filename, image_link, path)

        else:
            image_link, filetype = self.get_image_link(album)
            filename = image_link[image_link.rfind('/') + 1:]
            logger.info('Downloading gallery image: %s' % filename)
            Image().download(filename, image_link, path)

    def download_favorites(self, username, latest=True, page=0, max_items=None):
        logger.info("Getting account favorites")
        favorites = self.get_account_favorites(username=username,
                                               sort='oldest' if not latest else 'newest',
                                               page=page,
                                               max_items=max_items)
        logger.debug('Number of favorites: %d' % len(favorites))
        for favorite in favorites:
            self.parse_id(favorite['link'])

    def list_favorites(self, username, latest=True, page=0, max_items=-1):
        favorites = self.get_account_favorites(username=username,
                                               sort='oldest' if not latest else 'newest',
                                               page=page,
                                               max_items=max_items)
        logger.info(pformat(favorites))


class Tag(Downloadable):
    """
    Class which holds all the methods for downloading tags.
    """

    def download(self, id, page=0, max_items=30):

        logger.debug('Getting tag details')
        items = self.get_tag(id, page=page, max_items=max_items)

        # For each item in tag. Items are "albums"
        for item in items:

            if 'images' in item:
                tag_root_title = item['title'] if item['title'] else item['id']
                tag_root_title = self.replace_characters(tag_root_title)
                tag_root_path = os.path.join(
                    self.get_download_path(), tag_root_title)
                self.mkdir(tag_root_path)

                for position, sub_image in enumerate(item['images'], start=1):
                    title = sub_image['title'] if sub_image['title'] else sub_image['id']
                    title = self.replace_characters(title)
                    path = os.path.join(tag_root_path, title)

                    self.mkdir(path)

                    logger.info('Downloading tag: %s' % title)
                    image_link, filetype = self.get_image_link(sub_image)
                    image_filename = "{} - {}{}".format(
                        sub_image['id'], position, filetype)
                    Image().download(image_filename, image_link, path)

            else:
                title = item['title'] if item['title'] else item['id']
                title = self.replace_characters(title)
                path = os.path.join(self.get_download_path(), title)

                self.mkdir(path)

                logger.info('Downloading tag: %s' % title)
                image_link, filetype = self.get_image_link(sub_image)
                image_filename = "{} - {}{}".format(
                    sub_image['id'], position, filetype)
                Image().download(image_filename, image_link, path)

    def get_tag(self, tag, sort='top', window='week', page=0, max_items=30):
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }

        items = []
        url = f'gallery/t/{tag}/{sort}/{window}/{page}'
        response = self._api.get(url, headers)

        while len(response) != 0 and len(items) < max_items:
            for item in response['items']:
                items.append(item)

            url = f'gallery/t/{tag}/{sort}/{window}/{page}'
            logger.debug('Url to download: %s' % url)
            response = self._api.get(url, headers)
            page += 1
        return items[:max_items + 1]


class Subreddit(Downloadable):
    """
    Class which holds all the methods for downloading subreddits.
    """

    def get_metadata(self, subreddit, sort='time', window='day', page=0):
        url = f'gallery/r/{subreddit}/{sort}/{window}/{page}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        return self._api.get(url, headers=headers)

    def get_image(self, subreddit, image_id):
        url = f'gallery/r/{subreddit}/{image_id}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        return self._api.get(url, headers=headers)

    def download_from_subreddit(self, subreddit, id):

        logger.debug('Getting subreddit gallery details')
        subreddit_album = self.get_subreddit_image(subreddit, id)['data']
        title = subreddit_album['title'] if subreddit_album['title'] else subreddit_album['id']
        title = self.replace_characters(title)
        path = self.get_download_path()

        logger.debug("Checking if folder exists")
        if not os.path.exists(path):
            logger.debug("Creating folder: %s" % path)
            os.makedirs(path)

        logger.info('Downloading subreddit gallery image: %s' % title)
        image_link, filetype = self.get_image_link(subreddit_album)
        filename = image_link[image_link.rfind('/') + 1:]
        Image().download(filename, image_link, self.get_download_path())

    def download(self, subreddit, sort='time', window='day', page=0, max_items=30):
        logger.debug("Getting subreddit details")
        subreddit_data = []
        response = self.get_subreddit_gallery(
            subreddit, sort=sort, window=window, page=page)['data']  # TODO: use .get()

        while len(subreddit_data) < max_items and len(response) != 0:
            subreddit_data += response
            page += 1
            response = self.get_subreddit_gallery(
                subreddit, sort, window, page)['data']

        logger.debug("Sending subreddit items to parse_id")
        for position, item in enumerate(subreddit_data):
            if position + 1 <= max_items:
                self.parse_id(item["link"], page, max_items)
