import os
import re
import webbrowser
from abc import ABC, abstractmethod
from dataclasses import dataclass
from os.path import exists, join
from pathlib import Path
from pprint import pformat
from time import sleep
from typing import Any, Dict, List, Optional, Union

import logs
import requests

from imgurtofolder.imgur import ImgurAPI

log = logs.Log('objects')


@dataclass
class Downloadable(ABC):
    """
    Abstract class which holds all the common methods for downloading images and albums.
    """
    url: str
    title: str

    @abstractmethod
    def get_metadata(self, **kwargs):
        """
        Gets the metadata for the object using the API.
        """
        ...

    @abstractmethod
    def download(self, overwrite: bool = False, **kwargs):
        """
        Downloads the multi-media blob.
        """
        ...


class Image(Downloadable):
    """
    Class which holds all the methods for downloading images.
    """

    api: ImgurAPI

    def _get_image_link(self, image):
        """
        Gets the link to the image from the image metadata

        Parameters:
            image (dict): The image metadata

        Returns:
            tuple: The link to the image and the extension of the image
        """

        _filetypes = {
            'mp4': '.mp4',
            'gifv': '.gif',
            'link': lambda item: Path(item['link']).suffix,
        }

        for filetype, extension in _filetypes.items():
            if filetype in image:
                return image[filetype], extension
        else:
            raise ValueError('Unknown filetype')

    def download(self, path, overwrite: bool = False, **kwargs):
        """
        Downloads a file from a url to a path

        Parameters:
            filename (str): The name of the file to be downloaded
            url (str): The url of the file to be downloaded
            path (str): The path to download the file to
        """

        filename = self.title + self._get_image_link(self.get_metadata())[1]

        if not exists(path):
            log.debug('Creating folder path for image {join(path, "/",  filename)}')
            os.makedirs(path)

        if not overwrite and exists(join(path, filename)):
            log.info(f'\tSkipping {filename} because it already exists')
            return

        response: requests.Response = self.api.get(
            self.url,
            return_raw_response=True,
            stream=True
        )
        if not response.status_code == 200:
            log.info(f'\tERROR! Can not download: {join(path, filename)}')
            log.info(f'\tStatus code: {response.status_code}')

        file_size = int(response.headers.get(
            'content-length', 0)) / float(1 << 20)
        log.info('\t%s, File Size: %.2f MB' % (filename, file_size))
        with open(join(path, filename), 'wb') as image_file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, image_file)

        # TODO: Replace this old way of sleeping to avoid rate limit to use a calculated wait based on the rate limit
        sleep(.1)


class Album(Downloadable):
    """
    Class which holds all the methods for downloading albums.
    """
    images: List[Image]

    def get_metadata(self, album_hash):
        url = f'album/{album_hash}'
        headers = {
            'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
        }
        return self._api.get(url, headers=headers)

    def download(self, id):

        log.debug('Getting album details')
        album = self.get_album(id)['data']
        title = album['title'] if album['title'] else album['id']
        title = self.replace_characters(title)
        path = os.path.join(self.get_download_path(), title)

        log.debug("Checking if folder exists")
        if not os.path.exists(path):
            log.debug("Creating folder: %s" % path)
            os.makedirs(path)

        log.info('Downloading album: %s' % title)
        for position, image in enumerate(album['images'], start=1):
            image_link, filetype = self.get_image_link(image)
            image_filename = "{} - {}{}".format(
                album['id'], position, filetype)

            Image().download(image_filename, image_link, path)


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

        log.debug('Getting Gallery details')
        album = self.get_gallery_album(id)['data']
        title = album['title'] if album['title'] else album['id']
        title = self.replace_characters(title)
        path = os.path.join(self.get_download_path(), title)

        log.debug("Checking if folder exists")
        if not os.path.exists(path):
            log.debug("Creating folder: %s" % path)
            os.makedirs(path)

        if 'images' in album:
            log.info('Downloading gallery %s' % album['id'])
            for position, image in enumerate(album['images'], start=1):
                image_link, filetype = self.get_image_link(image)
                filename = album['id'] + ' - ' + str(position) + filetype
                Image().download(filename, image_link, path)

        else:
            image_link, filetype = self.get_image_link(album)
            filename = image_link[image_link.rfind('/') + 1:]
            log.info('Downloading gallery image: %s' % filename)
            Image().download(filename, image_link, path)

    def download_favorites(self, username, latest=True, page=0, max_items=None):
        log.info("Getting account favorites")
        favorites = self.get_account_favorites(username=username,
                                               sort='oldest' if not latest else 'newest',
                                               page=page,
                                               max_items=max_items)
        log.debug('Number of favorites: %d' % len(favorites))
        for favorite in favorites:
            self.parse_id(favorite['link'])

    def list_favorites(self, username, latest=True, page=0, max_items=-1):
        favorites = self.get_account_favorites(username=username,
                                               sort='oldest' if not latest else 'newest',
                                               page=page,
                                               max_items=max_items)
        log.info(pformat(favorites))


class Tag(Downloadable):
    """
    Class which holds all the methods for downloading tags.
    """

    def download(self, id, page=0, max_items=30):

        log.debug('Getting tag details')
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

                    log.info('Downloading tag: %s' % title)
                    image_link, filetype = self.get_image_link(sub_image)
                    image_filename = "{} - {}{}".format(
                        sub_image['id'], position, filetype)
                    Image().download(image_filename, image_link, path)

            else:
                title = item['title'] if item['title'] else item['id']
                title = self.replace_characters(title)
                path = os.path.join(self.get_download_path(), title)

                self.mkdir(path)

                log.info('Downloading tag: %s' % title)
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
            log.debug('Url to download: %s' % url)
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

        log.debug('Getting subreddit gallery details')
        subreddit_album = self.get_subreddit_image(subreddit, id)['data']
        title = subreddit_album['title'] if subreddit_album['title'] else subreddit_album['id']
        title = self.replace_characters(title)
        path = self.get_download_path()

        log.debug("Checking if folder exists")
        if not os.path.exists(path):
            log.debug("Creating folder: %s" % path)
            os.makedirs(path)

        log.info('Downloading subreddit gallery image: %s' % title)
        image_link, filetype = self.get_image_link(subreddit_album)
        filename = image_link[image_link.rfind('/') + 1:]
        Image().download(filename, image_link, self.get_download_path())

    def download(self, subreddit, sort='time', window='day', page=0, max_items=30):
        log.debug("Getting subreddit details")
        subreddit_data = []
        response = self.get_subreddit_gallery(
            subreddit, sort=sort, window=window, page=page)['data']  # TODO: use .get()

        while len(subreddit_data) < max_items and len(response) != 0:
            subreddit_data += response
            page += 1
            response = self.get_subreddit_gallery(
                subreddit, sort, window, page)['data']

        log.debug("Sending subreddit items to parse_id")
        for position, item in enumerate(subreddit_data):
            if position + 1 <= max_items:
                self.parse_id(item["link"], page, max_items)
