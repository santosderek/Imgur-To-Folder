# 3rd party modules
import imgurpython as ip
import requests
# Python modules
import os
import shutil
import re

import logging
from time import sleep

# Constants:

# Number of bytes in a megabyte
MBFACTOR = float(1 << 20)


logging.getLogger("requests").setLevel(logging.WARNING)

""" Setting up logging """
logging.basicConfig(level=logging.DEBUG,
                    format="[%(levelname)s] %(asctime)s: %(message)s",
                    datefmt='%I:%M:%S %p')

LOGGER = logging.getLogger('imgurtofolder')


class Imgur_Downloader:
    def __init__(self,
                 client_id,
                 client_secret,
                 folder_path,
                 refresh_token=None,
                 single_images_folder=True):

        # Correcting refesh token
        if not refresh_token:
            refresh_token = None

        # Storing refresh token
        self.refresh_token = refresh_token

        self.single_images_folder = single_images_folder

        # Creating ImgurClient
        self.client = ip.ImgurClient(client_id,
                                     client_secret,
                                     refresh_token=refresh_token)

        # Setting desired folder path
        self.desired_folder_path = self.check_folder_path(folder_path)
        self.check_if_folder_exists()

        # If refresh_token was given, set true
        if self.refresh_token is not None:
            self.is_authenticated = True
        else:
            self.is_authenticated = False

    def check_if_folder_exists(self):
        """ Checks if folder exists, and creates one if not """
        if not os.path.exists(self.desired_folder_path):
            os.mkdir(self.desired_folder_path)

    def parse_for_gallery_id(self, url):

        # Base url path for gallery and album
        # If base url path ever changes only need to change these two variables

        if re.search(r'imgur\.com/(a/\w+|gallery/\w+)', url) is None:
            return None

        album = 'imgur.com/a/'
        gallery = 'imgur.com/gallery/'

        if url.find(album) != -1:
            start_position = int(url.find(album) + len(album))

        elif url.find(gallery) != -1:
            start_position = int(url.find(gallery) + len(gallery))

        if start_position != -1:
            end_position = int(url.find('/', start_position))
            if (end_position > -1):
                return url[start_position:end_position]
            else:
                return url[start_position:]

    def replace_characters(self, word):
        # NOTE: '\\/:*?"<>|.' are invalid folder characters in a file system
        invalid_characters = ['\\', "'", '/', ':',
                              '*', '?', '"', '<', '>', '|', '.']

        for character in invalid_characters:
            word = word.replace(character, '')

        return word

    def check_folder_path(self, path):
        # Checks if the last char of path has a '/' to complete the extension
        path = path.replace('\\', '/')

        if path[-1:] != '/':
            path += '/'
        return path

    def authenticate(self):

        if self.refresh_token is not None:
            return

        # Get config.py file
        location = os.path.dirname(os.path.abspath(__file__))
        location = self.check_folder_path(location)
        location += 'config.py'

        # LOGGER.debug(location)

        # Communicating to user

        LOGGER.debug(
            'Please go to specified URL: (Imgur-To-Folder does NOT collect any username or password data)')
        LOGGER.debug(str(self.client.get_auth_url('pin')))

        pin = str(input('Plase type or paste the pin given here:'))

        # Authenicate
        credentials = self.client.authorize(pin, 'pin')
        self.client.set_user_auth(credentials['access_token'],
                                  credentials['refresh_token'])

        # Read config.py
        with open(location, 'r') as config_file:
            data = config_file.readlines()

        # Look for Refresh_Token line
        count = 0
        found_line_number = None
        for line in data:

            if line.find('refresh_token') != -1:
                found_line_number = count

            count += 1

        # Replace the line
        if found_line_number is not None:
            line = '\t\'refresh_token\': \'%s\',\n' % credentials['refresh_token']
            data[found_line_number] = line

        # Write it back into the file
        with open(location, 'w') as config_file:
            config_file.writelines(data)

    def detect_automatically(self, url=None):

        if not url:
            return

        response = self.parse_for_gallery_id(url)

        if response is not None:
            self.download_album(response)

        elif re.search(r'imgur\.com/(\w+$)', url) is not None:
            value = re.search(r'imgur\.com/(\w+$)', url).group(0)
            value = value.replace('imgur.com/', '')

            image_class = self.client.get_image(value)
            LOGGER.info('Downloading image: ' + str(url))
            self.download_image(image_class.link)

        else:
            LOGGER.info('Downloading image: ' + str(url))
            self.download_image(url)
            # LOGGER.info('Finished image: ' + str(url))

    def paginate_favorites(self, favorites):
        """ Creates a new list of nested lists containing no more than 10 items """
        length = len(favorites)

        new_list = []

        for current_number in range(0, length, 10):
            if length - current_number <= 10:
                new_list.append(favorites[current_number:])
            else:
                new_list.append(favorites[current_number:current_number + 10])

        return new_list

    def list_favorites_pages(self, username):

        favorites = self.client.get_account_favorites(username)

        LOGGER.info('Found %d favorites' % len(favorites))

        for position, page in enumerate(self.paginate_favorites(favorites)):
            LOGGER.info('--------- [PAGE %d] ---------', position)

            for selection in page:
                LOGGER.info('\t%s', selection.link)

    def download_favorites(self, username, starting_page=0, ending_page=-1):
        """ Download all favorites within username. Each 'Page' will be 10 favorites """

        # Get list of favorites from specified user
        not_paginated_favorites = self.client.get_account_favorites(username)
        paginated_favorites = self.paginate_favorites(not_paginated_favorites)

        # Display the length of favorites
        LOGGER.info('Found %d favorites' % len(not_paginated_favorites))
        sleep(1)

        # Trim the ammount of favorites specified from the user
        if ending_page != -1 and starting_page >= 0:
            favorites = paginated_favorites[starting_page:ending_page]
        else:
            favorites = paginated_favorites[starting_page:]

        # Loop through all favorites, parse id, and download the file.
        for position, page in enumerate(favorites, 1):
            LOGGER.info('--------- [PAGE %d] ---------',
                        starting_page + position)

            for selection in page:
                ID = self.parse_for_gallery_id(selection.link)
                # If an album
                if ID is not None:
                    self.download_album(ID)
                # If an image
                else:
                    LOGGER.info('Downloading single image: ' +
                                str(selection.link))
                    self.download_image(selection.link)
                    # LOGGER.info('Finished single image: ' + str(selection.link))

    def download_album(self, ID):

        if not ID:
            LOGGER.debug('ERROR: No album link given')
            return

        # Try to get album_title
        try:
            album_title = self.client.get_album(ID).title
        except ip.helpers.error.ImgurClientError:
            album_title = None

        # If album_title is None after trying it's album object,
        # Then maybe it's a gallery.
        if not album_title:
            try:
                album_title = self.client.gallery_item(ID).title
            except ip.helpers.error.ImgurClientError:
                album_title = None

        # If album_title is None at this point,
        # Then use it's section as it's album name
        if not album_title:
            # Try to get album section, to use later
            try:
                section = self.client.get_album(ID).section
            except ip.helpers.error.ImgurClientError:
                section = None

            # If section was given at any point earlier,
            # Then, use it to find the title
            # unless exception, make album_title = None
            if section is not None:
                try:
                    album_title = self.client.subreddit_image(
                        section, ID).title
                except ip.helpers.error.ImgurClientError:
                    album_title = None

        # If album_title still equals None, make the album title the ID
        if album_title is None:
            album_title = ID

        # Look for invalid characters
        album_title = self.replace_characters(album_title)

        # Alert the user
        LOGGER.info('Downloading album: ' + album_title)

        # Try to see if it is an album
        for position, image in enumerate(self.client.get_album(ID).images):
            try:
                self.download_image(image['link'], album_title, position + 1)

            except ip.helpers.error.ImgurClientError as e:
                LOGGER.debug(
                    'ERROR: Could not finish album download' + str(image['link']) + str(e))
        # LOGGER.info('Finished album: ' + album_title)

    def download_image(self, url='', directory_name=None, album_position=0):

        # Max length of a file name [Windows]
        MAX_NAME_LENGTH = 65

        # Changes .gifv links to .gif since imgur supports this transfer
        if url[-4:] == 'gifv':
            url = url[:-4] + 'gif'

        req = requests.get(url, stream=True)

        if req.status_code == 200:

            # Link names
            if album_position == 0:
                link_name = url[url.rfind('/') + 1:]

            else:
                # First erase invalid characters
                link_name = directory_name[:MAX_NAME_LENGTH] + \
                    ' - ' + str(album_position)
                link_name = self.replace_characters(link_name)

                # Then add file_extension
                file_extension = url[url.rfind('.'):]
                link_name += file_extension

            # If directory_name is given, make it the new folder name
            if directory_name is not None:

                if len(directory_name) > MAX_NAME_LENGTH:
                    directory_name = directory_name[:MAX_NAME_LENGTH]

                directory_name = self.replace_characters(directory_name)

                # If directory not given then get the absolute path.
                # This is done since I had problems using relative paths during testing.
                # Needed to make sure it was given a absolute path.
                if self.desired_folder_path == '.' or self.desired_folder_path == './':
                    absolute_path = self.check_folder_path(os.getcwd())
                    directory_name = absolute_path + directory_name
                else:
                    directory_name = self.desired_folder_path + directory_name

                directory_name = self.check_folder_path(directory_name)

            # Else make the desired_folder_path the folder to download in
            elif self.single_images_folder:
                directory_name = self.desired_folder_path + 'Single-Images/'

            else:
                directory_name = self.desired_folder_path

            # Make directory if not existed
            if not os.path.exists(directory_name):
                os.makedirs(directory_name)

            elif os.path.exists(directory_name + link_name):
                LOGGER.info('\tSkipping: ' + directory_name + link_name)
                return

            # Download image to path + file name
            file_size = req.headers.get('content-length', 0)
            LOGGER.info('\t%s, File Size: %.2f MB',
                        link_name,
                        int(file_size) / MBFACTOR)
            with open(directory_name + link_name, 'wb') as image_file:
                req.raw.decode_content = True
                shutil.copyfileobj(req.raw, image_file)
        else:
            LOGGER.debug('ERROR: Could not find url! ' + str(url))

    def change_folder(self, folder_path):
        self.desired_folder_path = self.check_folder_path(folder_path)
