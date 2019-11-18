# Derek Santos
import logs
import os
from pprint import pformat
import re
import requests
import shutil
from time import sleep
import json
from imgur import Imgur
log = logs.Log('downloader')

class Imgur_Downloader(Imgur):
    def __init__(self, configuration, max_favorites):

        super().__init__(configuration)
        self._max_favorites = max_favorites

    def replace_characters(self, word):
        # NOTE: '\\/:*?"<>|.' are invalid folder characters in a file system
        invalid_characters = ['\\', "'", '/', ':',
                              '*', '?', '"', '<',
                              '>', '|', '.', '\n']

        for character in invalid_characters:
            word = word.replace(character, '')

        return word

    def parse_id(self, url, page=0, max_items=30):
        imgur_base_extensions = {
            'album' : [r'(/a/)(\w+)'],
            'gallery' : [r'(/g/)(\w+)', r'(/gallery/)(\w+)'],
            'subreddit' : [r'(/r/)(\w+)\/(\w+)'],
            'tag' : [r'(/t/)(\w+)']
        }

        if any(re.search(item, url) for item in imgur_base_extensions['album']):
            for item in imgur_base_extensions['album']:
                result = re.search(item, url).group(2) if re.search(item, url) else None
                if result:
                    self.download_album(result)

        elif any(re.search(item, url) for item in imgur_base_extensions['gallery']):
            for item in imgur_base_extensions['gallery']:
                result = re.search(item, url).group(2) if re.search(item, url) else None
                if result:
                    self.download_gallery(result)

        elif any(re.search(item, url) for item in imgur_base_extensions['subreddit']):
            for item in imgur_base_extensions['subreddit']:
                if re.search(item, url):
                    subreddit, id = re.search(item, url).group(2), re.search(item, url).group(3)
                    self.download_subreddit_gallery(subreddit, id)

        elif any(re.search(item, url) for item in imgur_base_extensions['tag']):
            for item in imgur_base_extensions['tag']:
                result = re.search(item, url).group(2) if re.search(item, url) else None
                if result:
                    self.download_tag(result, page=page, max_items=max_items)

        else:
            log.info('Downloading image: %s' % url[url.rfind('/') + 1:])
            self.download(url[url.rfind('/') + 1:], url, self.get_download_path())

    def get_image_link(self, image):
        if 'mp4' in image:
            image_link = image['mp4']
            filetype = '.mp4'
        elif 'gifv' in image:
            image_link = image['gifv']
            filetype = '.gif'
        else:
            image_link = image['link']
            filetype = image_link[image_link.rfind('.'):]

        return image_link, filetype

    def mkdir(self, path):
        log.debug("Checking if folder exists")
        if not os.path.exists(path):
            log.debug("Creating folder: %s" % path)
            os.mkdir(path)

    def download_tag(self, id, page=0, max_items=30):
        log.debug('Getting tag details')
        items = self.get_tag(id, page=page, max_items=max_items)

        # For each item in tag. Items are "albums"
        for item in items:

            if 'images' in item:
                tag_root_title = item['title'] if item['title'] else item['id']
                tag_root_title = self.replace_characters(tag_root_title)
                tag_root_path  = os.path.join(self.get_download_path(), tag_root_title)
                self.mkdir(tag_root_path)

                for position, sub_image in enumerate(item['images'], start=1):
                    title = sub_image['title'] if sub_image['title'] else sub_image['id']
                    title = self.replace_characters(title)
                    path  = os.path.join(tag_root_path, title)

                    self.mkdir(path)

                    log.info('Downloading tag: %s' % title)
                    image_link, filetype = self.get_image_link(sub_image)
                    image_filename = "{} - {}{}".format(sub_image['id'], position, filetype)
                    self.download(image_filename, image_link, path)

            else:
                title = item['title'] if item['title'] else item['id']
                title = self.replace_characters(title)
                path  = os.path.join(self.get_download_path(), title)

                self.mkdir(path)

                log.info('Downloading tag: %s' % title)
                image_link, filetype = self.get_image_link(sub_image)
                image_filename = "{} - {}{}".format(sub_image['id'], position, filetype)
                self.download(image_filename, image_link, path)


    def download_album(self, id):

        log.debug('Getting album details')
        album = self.get_album(id)['data']
        title = album['title'] if album['title'] else album['id']
        title = self.replace_characters(title)
        path  = os.path.join(self.get_download_path(), title)

        log.debug("Checking if folder exists")
        if not os.path.exists(path):
            log.debug("Creating folder: %s" % path)
            os.mkdir(path)

        log.info('Downloading album: %s' % title)
        for position, image in enumerate(album['images'], start=1):
            image_link, filetype = self.get_image_link(image)
            image_filename = "{} - {}{}".format(image['id'], position, filetype)

            # log.info('\tDownloading %s' % image_filename)
            self.download(image_filename, image_link, path)


    def download_gallery(self, id):

        log.debug('Getting Gallery details')
        album = self.get_gallery_album(id)['data']
        title = album['title'] if album['title'] else album['id']
        title = self.replace_characters(title)
        path  = os.path.join(self.get_download_path(), title)

        log.debug("Checking if folder exists")
        if not os.path.exists(path):
            log.debug("Creating folder: %s" % path)
            os.mkdir(path)

        if 'images' in album:
            log.info('Downloading gallery %s' % album['id'])
            for position, image in enumerate(album['images'], start=1):
                image_link, filetype = self.get_image_link(image)
                filename = album['id'] + ' - ' + str(position) + filetype
                # log.info("\tDownloading %s" % filename)
                self.download(filename, image_link, path)

        else:
            image_link, filetype = self.get_image_link(album)
            filename = image_link[image_link.rfind('/') + 1:]
            log.info('Downloading gallery image: %s' % filename)
            self.download(filename, image_link, path)


    def download_subreddit_gallery(self, subreddit, id):

        log.debug('Getting subreddit gallery details')
        subreddit_album = self.get_subreddit_image(subreddit, id)['data']
        title = subreddit_album['title'] if subreddit_album['title'] else subreddit_album['id']
        title = self.replace_characters(title)
        path  = self.get_download_path()

        log.debug("Checking if folder exists")
        if not os.path.exists(path):
            log.debug("Creating folder: %s" % path)
            os.mkdir(path)

        log.info('Downloading subreddit gallery image: %s' % title)
        image_link, filetype = self.get_image_link(subreddit_album)
        filename = image_link[image_link.rfind('/') + 1:]
        self.download(filename, image_link, self.get_download_path())


    def download_favorites(self, username, latest=True, page=0, max_items=None):
        log.info("Getting account favorites")
        favorites = self.get_account_favorites(username = username,
                                                      sort = 'oldest' if not latest else 'newest',
                                                      page=page,
                                                      max_items=max_items)
        log.debug('Number of favorites: %d' % len(favorites))
        for favorite in favorites:
            self.parse_id(favorite['link'])

    def list_favorites(self, username, latest=True, page=0, max_items=-1):
        favorites = self.get_account_favorites(username = username,
                                                      sort = 'oldest' if not latest else 'newest',
                                                      page=page,
                                                      max_items=max_items)
        log.info(pformat(favorites))

    def download_account_images(self, username, page=0, max_items=None):
        account_images = self.get_account_images(username, page=page)

        if max_items:
            account_images = account_images[:max_items]

        for image in account_images:
            self.parse_id(image['link'])

    def download(self, filename, url, path):

        log.debug('Checking that folder path exists')
        if not os.path.exists(path):
            los.debug('Creating folder path')
            os.mkdir(path)

        log.debug('Checking to overwrite')
        if not self.get_overwrite() and os.path.exists(os.path.join(path, filename)):
            log.info('\tSkipping %s' % filename)
            return

        req = requests.get(url, stream=True)
        if req.status_code == 200:
            file_size = int(req.headers.get('content-length', 0)) / float(1 << 20)
            log.info('\t%s, File Size: %.2f MB' % (filename, file_size))
            with open(os.path.join(path, filename), 'wb') as image_file:
                req.raw.decode_content = True
                shutil.copyfileobj(req.raw, image_file)
        else:
            log.info('\tERROR! Can not download: ' + os.path.join(path, filename))
            log.info('\tStatus code: ' + str(req.status_code))

        # Delaying so no timeout
        sleep(.1)
