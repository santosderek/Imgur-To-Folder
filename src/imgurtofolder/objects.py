from abc import ABC, abstractmethod
from typing import Optional
from imgurtofolder.constants import IMGUR_BASE_EXTENSIONS
import os
from pathlib import Path
from pprint import pformat, pprint
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

    def __init__(self, id: str, api: ImgurAPI):
        self.id = id
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
            url=f"image/{self.id}",
            headers={
                "Authorization": f"Client-ID {self.api._configuration.client_id}",
            }
        ).get('data')

    async def download(self, path: Optional[str] = None, overwrite: bool = False, enumeration: Optional[int] = None):
        """
        Downloads a file from a url to a path

        Parameters:
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

        _path = Path(
            path
            or
            self.api._configuration.download_path
        )

        if not _path.exists():
            logger.debug(f'Creating folder path {_path}')
            _path.mkdir(parents=True, exist_ok=True)

        _full_path = _path / _filename

        if not overwrite and _full_path.exists():
            logger.info(f'Skipping {_full_path} because it already exists')
            return

        response: requests.Response = self.api.get(
            _url,
            return_raw_response=True,
            stream=True
        )

        if response.status_code != 200:
            logger.error('Error downloading image: %s' % pformat(response.json()))
            raise ValueError(f'Error downloading image: {self.id}')

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
            url=f"album/{self.id}",
            headers={
                "Authorization": f"Client-ID {self.api._configuration.client_id}",
            }
        ).get('data')

    async def download(self, overwrite: bool = False):

        metadata = self.get_metadata()

        _title = replace_characters(metadata.get('title') or metadata.get('id'))
        _path = Path(self.api._configuration.download_path) / _title

        logger.debug("Checking if folder exists")
        _path.mkdir(parents=True, exist_ok=True)

        logger.info('Downloading album: %s' % _title)

        _images = metadata.get('images') or []

        _futures = []
        for position, image in enumerate(_images, start=1):
            _futures.append(
                asyncio.create_task(
                    Image(
                        id=image.get('id'),
                        api=self.api
                    ).download(
                        path=_path,
                        overwrite=overwrite,
                        enumeration=position
                    )
                )
            )
        await asyncio.gather(*_futures)


class Gallery(Album):
    """
    Class which holds all the methods for downloading galleries.
    """

    def get_metadata(self, **kwargs):
        """
        Gets the metadata for the image using the API.

        Returns:
            dict: The metadata for the image
        """
        return self.api.get(
            f'gallery/{self.id}',
            headers={
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id
            }
        ).get('data')


class Account:

    def __init__(self, username: str, api: ImgurAPI):
        self.username = username
        self.api = api

    def get_account_submissions(self):
        """
        Get all submissions from an account

        Parameters:
            username (str): The username of the account

        Returns:
            list: A list of all submissions from the account
        """
        return self.api.get(
            f'account/{self.username}/submissions/',
            {
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id,
            }
        )

    async def get_account_favorites(self, username, sort='newest', page=0, max_items=-1):
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

        async def _get_next_page(username: str, page: int, sort: str):
            """
            Gets the next page of favorites

            Parameters:
                username (str): The username of the account
                page (int): The page number to start on
                sort (str): The sort order of the favorites
            """
            logger.info(f'Getting page {page} of favorites')
            _response = self.api.get(
                f'account/{username}/favorites/{page}/{sort}',
                headers={
                    'Authorization': f'Bearer {self.api._configuration.access_token}',
                }
            ).get('data')
            await asyncio.sleep(.05)
            return _response

        favorites = []

        while len(response := await _get_next_page(username, page, sort)) != 0:

            if len(favorites) > max_items:
                return favorites[:max_items]

            favorites.extend(response)
            page += 1

        return favorites


class Tag(Downloadable):
    """
    Class which holds all the methods for downloading tags.
    """

    def __init__(self, id: str, api: ImgurAPI):
        self.id = id
        self.api = api

    def get_metadata(self, sort='top', window='week', page=0):
        logger.info(f'Getting page {page} of favorites')
        _response = self.api.get(
            f'gallery/t/{self.id}/{sort}/{window}/{page}',
            headers={
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id
            }
        ).get('data')
        return _response

    async def download(self, starting_page: int = 0, max_items: int = 30):

        def get_items():

            items = []

            _page = starting_page

            while response := self.get_metadata(page=_page):

                _items = response.get('items') or []

                if (
                        len(response) == 0
                        or
                        len(items) > max_items
                ):
                    return items[:max_items]

                items.extend(_items)

                _page += 1

            return items[:max_items]

        logger.debug('Getting tag details')
        items = get_items()

        # For each item in tag. Items are "albums"
        futures = []
        for item in items:

            if item.get('is_album') is True:
                logger.info('Downloading album: %s' % item['title'])
                futures.append(
                    asyncio.create_task(
                        Album(
                            id=item['id'],
                            api=self.api
                        ).download()
                    )
                )

            else:
                logger.info('Downloading image: %s' % item['title'])
                futures.append(
                    asyncio.create_task(
                        Image(
                            id=item['id'],
                            api=self.api
                        ).download()
                    )
                )

        await asyncio.gather(*futures)


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
