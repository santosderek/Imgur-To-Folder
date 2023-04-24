import asyncio
import re
from dataclasses import dataclass
from logging import getLogger
from typing import Optional

from imgurtofolder.api import ImgurAPI
from imgurtofolder.constants import IMGUR_BASE_EXTENSIONS
from imgurtofolder.objects import (Account, Album, Gallery, Image,
                                   ImgurObjectResponse, ImgurObjectType,
                                   Subreddit)
from typing import List
logger = getLogger(__name__)


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
        return ImgurObjectResponse(
            id=re.search(IMGUR_BASE_EXTENSIONS['image'][0], url).group(3),
            type=ImgurObjectType.IMAGE
        )


async def download_urls(urls: List[str], api: ImgurAPI):
    """
    Download a list of urls.

    Parameters:
        urls (List[str]): The list of urls.
        api (ImgurAPI): The Imgur API object.
    """
    futures = []
    for url in urls:
        try:
            imgur_object: Optional[ImgurObjectResponse] = parse_id(url)

            if imgur_object is None:
                continue

            if imgur_object.type == ImgurObjectType.IMAGE:
                futures.append(
                    Image(imgur_object.id, api).download()
                )

            elif imgur_object.type == ImgurObjectType.ALBUM:
                futures.append(
                    Album(imgur_object.id, api).download()
                )

            elif imgur_object.type == ImgurObjectType.GALLERY:
                futures.append(
                    Gallery(imgur_object.id, api).download()
                )

            elif imgur_object.type == ImgurObjectType.TAG:
                futures.append(
                    Tag(imgur_object.id, api).download()
                )

            elif imgur_object.type == ImgurObjectType.SUBREDDIT:

                if imgur_object.id and imgur_object.subreddit:
                    futures.append(
                        Subreddit(imgur_object.id, api).download()
                    )
                else:
                    futures.append(
                        Subreddit(imgur_object.id, api).download_from_subreddit(imgur_object.subreddit)
                    )

        except Exception:
            logger.exception(f'Error with url {url}:')

    await asyncio.gather(*futures)


async def download_favorites(username: str, api: ImgurAPI, sort: str = 'newest', starting_page: int = 0, max_items: Optional[int] = None):
    """
    Downloads the favorites of the user

    Parameters:
        sort (str): The sort type
        page (int): The page to start on
        max_items (int): The maximum number of items to download
    """

    _args = {
        'page': starting_page,
        'sort': sort,
    }
    if max_items:
        _args['max_items'] = max_items

    favorites = await Account(username, api).get_account_favorites(username, **_args)

    futures = []
    for favorite in favorites:
        if favorite['is_album']:
            futures.append(
                Album(favorite['id'], api).download()
            )

        else:
            futures.append(
                Image(favorite['id'], api).download()
            )

    await asyncio.gather(*futures)


async def download_account_images(username: str, api: ImgurAPI, starting_page: int = 0, max_items: int = 30):
    account_images = await Account(username, api).get_account_images(username, starting_page=starting_page, max_items=max_items)
    await download_urls([image['link'] for image in account_images], api)
