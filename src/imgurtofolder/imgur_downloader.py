import os
from os.path import basename
import re
from urllib.parse import urlparse

from imgurtofolder.objects import Album, Gallery, Image, Subreddit
from logging import getLogger

from imgurtofolder.constants import IMGUR_BASE_EXTENSIONS

logger = getLogger(__name__)


def mkdir(path):
    logger.debug("Checking if folder exists")
    if not os.path.exists(path):
        logger.debug("Creating folder: %s" % path)
        os.makedirs(path)




class Imgur_Downloader:


    def __init__(self, configuration):
        self._configuration = configuration

    def download_album(self, url) -> Album:
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

        if any(re.search(item, url) for item in IMGUR_BASE_EXTENSIONS['album']):
            self.download_album(url)

        elif any(re.search(item, url) for item in IMGUR_BASE_EXTENSIONS['gallery']):
            for item in IMGUR_BASE_EXTENSIONS['gallery']:
                result = re.search(item, url).group(
                    2) if re.search(item, url) else None
                if result:
                    Gallery(url,).download(result)

        elif any(re.search(item, url) for item in IMGUR_BASE_EXTENSIONS['subreddit']):
            for item in IMGUR_BASE_EXTENSIONS['subreddit']:
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

        elif any(re.search(item, url) for item in IMGUR_BASE_EXTENSIONS['tag']):
            for item in IMGUR_BASE_EXTENSIONS['tag']:
                result = re.search(item, url).group(
                    2) if re.search(item, url) else None
                if result:
                    Tag(url).download(
                        result,
                        page=page,
                        max_items=self._configuration.max_items
                    )

        else:
            logger.info(f'Downloading image: {basename(urlparse(url).path)}')
            Image(url, basename(urlparse(url).path)).download(
                self.get_download_path()
            )

    def download_account_images(self, username, page=0, max_items=None):
        account_images = self.get_account_images(username, page=page)

        if max_items:
            account_images = account_images[:max_items]

        for image in account_images:
            self.parse_id(image['link'])
