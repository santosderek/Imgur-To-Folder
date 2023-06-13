import asyncio
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from imgurtofolder.api import ImgurAPI

logger = getLogger(__name__)


class ImgurObjectType(Enum):
    ALBUM = 1
    GALLERY = 2
    SUBREDDIT = 3
    TAG = 4
    IMAGE = 5


@dataclass
class ImgurObjectResponse:

    id: str
    type: ImgurObjectType
    subreddit: Optional[str] = None


##### Helper functions #####

def replace_characters(word):
    # NOTE: '\\/:*?"<>|.' are invalid folder characters in a file system
    invalid_characters = ['\\', "'", '/', ':',
                          '*', '?', '"', '<',
                          '>', '|', '.', '\n']

    for character in invalid_characters:
        word = word.replace(character, '')

    return word.strip()

##### Downloadables #####


class Downloadable(ABC):
    """
    Abstract class which holds all the common methods for downloading images and albums.
    """

    def __init__(self, id: str, api: ImgurAPI):
        self.id = id
        self.api = api

    @abstractmethod
    async def get_metadata(self, **kwargs):
        """
        Gets the metadata for the object using the API.
        """
        ...

    async def download(self, starting_page: int = 0, max_items: int = 30):
        """
        Downloads all items from current id.

        Parameters:
            starting_page (int): The page number to start on
            max_items (int): The maximum number of items to return
        """

        async def get_items():
            """
            Gets all items from current id.

            Returns:
                list: The items from the id
            """

            items = []
            _page = starting_page

            while response := await self.get_metadata(page=_page):

                _items = response

                if isinstance(_items, dict):
                    _items = response.get('items') or []

                items.extend(_items)

                if (
                        len(_items) == 0
                        or
                        len(items) > max_items
                ):
                    return _items[:max_items]

                _page += 1

            return items[:max_items]

        logger.debug(f'Getting {self.__class__.__name__} details')
        items = await get_items()

        futures = []
        for item in items:

            if item.get('is_album') is True:
                futures.append(
                    asyncio.create_task(
                        Album(
                            id=item['id'],
                            api=self.api
                        ).download()
                    )
                )

            else:
                futures.append(
                    asyncio.create_task(
                        Image(
                            id=item['id'],
                            api=self.api
                        ).download()
                    )
                )

        await asyncio.gather(*futures)


class Image(Downloadable):
    """
    Class which holds all the methods for downloading images.
    """

    async def get_metadata(self, **kwargs) -> Optional[dict]:
        """
        Gets the metadata for the image using the API.

        Returns:
            dict: The metadata for the image
        """

        meta = await self.api.get(
            url=f"image/{self.id}",
            headers={
                "Authorization": f"Client-ID {self.api._configuration.client_id}",
            }
        )
        return (meta or {}).get('data')

    async def download(self, path: Optional[str] = None, enumeration: Optional[int] = None) -> None:
        """
        Downloads a file from a url to a path

        Parameters:
            kwargs: Additional arguments

        Raises:
            ValueError: If the response code is not 200
        """

        metadata = await self.get_metadata()

        _title = metadata.get('title') or metadata.get('id')
        suffix = Path(metadata.get('link', '')).suffix
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

        if not self.api._configuration.overwrite and _full_path.exists():
            logger.info(f'Skipping {_full_path} because it already exists')
            return

        response: requests.Response = await self.api.get(
            _url,
            return_raw_response=True,
            include_default_headers=False,
            stream=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0',
            }
        )
        response.raise_for_status()

        file_size = int(response.headers.get('content-length', 0)) / float(1 << 20)

        logger.info('\t%s, File Size: %.2f MB' % (_full_path, file_size))

        with _full_path.open('wb') as image_file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, image_file)

        del response  # Dealocate the memory used in order to stream the file while we wait


class Album(Downloadable):
    """
    Class which holds all the methods for downloading albums.
    """

    async def get_metadata(self, **kwargs) -> Optional[dict]:
        """
        Gets the metadata for the image using the API.

        Returns:
            dict: The metadata for the image
        """
        meta = await self.api.get(
            url=f"album/{self.id}",
            headers={
                "Authorization": f"Client-ID {self.api._configuration.client_id}",
            }
        )
        return (meta or {}).get('data')

    async def download(self):

        metadata = await self.get_metadata()

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
                        enumeration=position
                    )
                )
            )
        await asyncio.gather(*_futures)


class Gallery(Album):
    """
    Class which holds all the methods for downloading galleries.
    """

    async def get_metadata(self, **kwargs) -> Optional[dict]:
        """
        Gets the metadata for the image using the API.

        Returns:
            dict: The metadata for the image
        """

        meta = await self.api.get(
            f'gallery/{self.id}',
            headers={
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id
            }
        )
        return (meta or {}).get('data')


class Tag(Downloadable):
    """
    Class which holds all the methods for downloading tags.
    """

    def __init__(self, id: str, api: ImgurAPI):
        """
        Parameters:
            id (str): The id of the tag
            api (ImgurAPI): The ImgurAPI object
        """
        self.id = id
        self.api = api

    async def get_metadata(self, sort: str = 'top', window: str = 'week', page: int = 0):
        """
        Gets the metadata for the image using the API.

        Parameters:
            sort (str): The sort order of the favorites
            window (str): The time window of the favorites
            page (int): The page number to start on
        """
        logger.info(f'Getting page {page} of favorites')

        meta = await self.api.get(
            f'gallery/t/{self.id}/{sort}/{window}/{page}',
            headers={
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id
            }
        )
        return (meta or {}).get('data')


class Subreddit(Downloadable):
    """
    Class which holds all the methods for downloading subreddits.
    """

    async def get_metadata(self, sort: str = 'time', window: str = 'day', page: int = 0) -> Optional[dict]:
        """
        Gets the metadata for the image using the API.

        Parameters:
            sort (str): The sort order of the favorites
            window (str): The window of the sort order
            page (int): The page number to start on
        """
        meta = await self.api.get(
            f'gallery/r/{self.id}/{sort}/{window}/{page}',
            headers={
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id
            }
        )
        return (meta or {}).get('data')

    async def get_image(self, subreddit: str, image_id: str) -> Optional[dict]:
        """
        Gets the metadata for the image using the API.

        Parameters:
            subreddit (str): The subreddit to get the image from
            image_id (str): The id of the image
        """
        meta = await self.api.get(
            f'gallery/r/{subreddit}/{image_id}',
            headers={
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id
            }
        )
        return (meta or {}).get('data')

    async def download_from_subreddit(self, subreddit: str) -> None:
        """
        Downloads an image from a subreddit

        Parameters:
            subreddit (str): The subreddit to get the image from
        """

        # FIXME: Half initailized module
        from imgurtofolder.downloader import download_urls

        logger.debug('Getting subreddit gallery details')
        subreddit = await self.get_image(subreddit, self.id)

        # TODO: This could be more efficient if we use the already fetched data instead of providing the link again
        await download_urls([item.get('link') for item in subreddit], self.api)


##### Account #####


class Account:

    def __init__(self, username: str, api: ImgurAPI):
        self.username = username
        self.api = api

    async def get_account_submissions(self) -> list:
        """
        Get all submissions from an account

        Parameters:
            username (str): The username of the account

        Returns:
            list: A list of all submissions from the account
        """

        meta = await self.api.get(
            f'account/{self.username}/submissions/',
            {
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id,
            }
        )
        return meta or []

    async def get_account_favorites(self, username: str, sort: str = 'newest', page: int = 0, max_items: int = -1) -> list:
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
            meta = await self.api.get(
                f'account/{username}/favorites/{page}/{sort}',
                headers={
                    'Authorization': f'Bearer {self.api._configuration.access_token}',
                }
            )
            return (meta or {}).get('data')

        favorites = []

        while len(response := await _get_next_page(username, page, sort)) != 0:

            favorites.extend(response)

            if len(favorites) > max_items:
                return favorites[:max_items]

            page += 1

        return favorites

    async def get_account_images(self, username: str, starting_page: int = 0, max_items: Optional[int] = None) -> list:
        """
        Get all images from an account

        Parameters:
            username (str): The username of the account
            page (int): The page number to start on

        Returns:
            list: A list of all images from the account
        """

        async def _get_next_page(_page):
            meta = await self.api.get(
                f'account/{username}/images/{_page}',
                headers={
                    'Authorization': f'Bearer {self.api._configuration.access_token}',
                }
            )
            return meta.get('data') or []

        account_images = []
        page = starting_page

        while len(response := await _get_next_page(page)) != 0:
            account_images.extend(response)

            if max_items is not None and len(account_images) > max_items:
                return account_images[:max_items]
            page += 1

        return account_images

    async def get_gallery_favorites(self, username: str, starting_page: int = 0, sort: str = 'newest') -> list:
        """
        Get all gallery favorites from an account

        Parameters:
            username (str): The username of the account
            sort (str): The sort order of the gallery favorites

        Returns:
            list: A list of all gallery favorites from the account
        """

        meta = await self.api.get(
            f'account/{username}/gallery_favorites/{starting_page}/{sort}',
            headers={
                'Authorization': 'Client-ID %s' % self.api._configuration.client_id,
            }
        )
        return meta or []
