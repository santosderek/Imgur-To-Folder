import re
from dataclasses import dataclass
from logging import getLogger
from os.path import basename
from typing import Optional
from urllib.parse import urlparse

from imgurtofolder.constants import IMGUR_BASE_EXTENSIONS
from imgurtofolder.objects import (Album, Gallery, Image, ImgurObjectType,
                                   Subreddit)

logger = getLogger(__name__)


@dataclass
class ImgurObjectResponse:

    id: str
    type: ImgurObjectType
    subreddit: Optional[str] = None


def parse_id(url: str) -> Optional[ImgurObjectResponse]:
    """
    Parses the url and returns a ImgurObjectResponse if it is a valid url

    Parameters:
        url (str): The url to parse
        page (int): The page to start on
        max_items (int): The maximum number of items to download
        sort (str): The sort type
        window (str): The window type
    """

    if any(re.search(item, url) for item in IMGUR_BASE_EXTENSIONS['album']):
        return ImgurObjectResponse(
            id=re.search(item, url).group(2),
            type=ImgurObjectType.ALBUM
        )

    elif any(re.search(item, url) for item in IMGUR_BASE_EXTENSIONS['gallery']):
        for item in IMGUR_BASE_EXTENSIONS['gallery']:
            _search = re.search(item, url)

            if not _search:
                continue

            return ImgurObjectResponse(
                id=_search.group(2),
                type=ImgurObjectType.GALLERY
            )

    elif any(re.search(item, url) for item in IMGUR_BASE_EXTENSIONS['subreddit']):
        for item in IMGUR_BASE_EXTENSIONS['subreddit']:

            _search = re.search(item, url)

            if not _search:
                continue

            subreddit = _search.group(2)
            id = _search.group(3) if re.compile(item).groups > 2 else None

            if id is None and subreddit is not None:
                return ImgurObjectResponse(
                    id=subreddit,
                    type=ImgurObjectType.SUBREDDIT
                )

            elif subreddit is not None and id is not None:
                return ImgurObjectResponse(
                    id=id,
                    type=ImgurObjectType.SUBREDDIT,
                    subreddit=subreddit
                )

    elif any(re.search(item, url) for item in IMGUR_BASE_EXTENSIONS['tag']):
        for item in IMGUR_BASE_EXTENSIONS['tag']:

            _search = re.search(item, url)

            if not _search:
                continue

            return ImgurObjectResponse(
                id=_search.group(2),
                type=ImgurObjectType.TAG
            )

    else:
        return None


def download_album(url) -> Album:
    """
    Downloads an album

    Parameters:
        url (str): The url to download
    """
    for item in IMGUR_BASE_EXTENSIONS['album']:
        result = re.search(item, url).group(2) \
            if re.search(item, url) else None
        if not result:
            ValueError("Could not parse album ID from URL")
        return Album(url).download(result)


def download_account_images(username, page=0, max_items=None):
    account_images = self.get_account_images(username, page=page)

    if max_items:
        account_images = account_images[:max_items]

    for image in account_images:
        self.parse_id(image['link'])
