# 3rd party modules
import imgurpython as ip
import requests
# Python modules
import os
import shutil
import re
import json
import logging
from time import sleep
# Imgur-To-Folder modules

""" Constants """

# Number of bytes in a megabyte
MBFACTOR = float(1 << 20)

AUTHORIZATION_URL = 'https://api.imgur.com/oauth2/authorize?client_id={CLIENT_ID}&response_type={RESPONSE_TYPE}&state=authorizing'
TOKEN_URL = 'https://api.imgur.com/oauth2/token'
ACCOUNT_FAVORITES_URL = 'https://api.imgur.com/3/account/{username}/favorites/{page_number}/{favoritesSort}'

# Get config.json file
CONFIG_LOCATION = os.path.dirname(os.path.abspath(__file__)) + '/config.json'


""" Setting up logging """
LOGGER = logging.getLogger('imgurtofolder')
LOGGER.setLevel(logging.DEBUG)


FORMATTER = logging.Formatter('[%(levelname)s] %(asctime)s: %(message)s',
                              datefmt='%I:%M:%S %p')

# Stream Handler for logging
STREAM_HANDLER = logging.StreamHandler()
STREAM_HANDLER.setLevel(logging.INFO)
STREAM_HANDLER.setFormatter(FORMATTER)

LOGGER.addHandler(STREAM_HANDLER)


def ENABLE_LOGGING_DEBUG():
    global STREAM_HANDLER
    STREAM_HANDLER.setLevel(logging.DEBUG)


class Imgur_Downloader:
    def __init__(self,
                 client_id,
                 client_secret,
                 folder_path,
                 refresh_token=None,
                 single_images_folder=True,
                 overwrite=False,
                 verbose=False,
                 max_favorites=None):
        if verbose:
            ENABLE_LOGGING_DEBUG()

        self.max_favorites = max_favorites

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
        self.change_desired_folder_path(folder_path)

        # If refresh_token was given, set true
        if self.refresh_token is not None:
            self.is_authenticated = True
        else:
            self.is_authenticated = False

        self.overwrite = overwrite

        # If verbose is selected, enable debug within logger.

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
                              '*', '?', '"', '<',
                              '>', '|', '.', '\n']

        for character in invalid_characters:
            word = word.replace(character, '')

        return word

    def check_folder_path(self, path):
        # Checks if the last char of path has a '/' to complete the extension
        path = path.replace('\\', '/')

        if path[-1:] != '/':
            path += '/'
        return path

    def parsing_redirected_link(self, redirected_link):
        refresh_token = None
        access_token = None

        # Searching for refresh_token
        search = re.search('refresh_token=\w+', redirected_link)

        if search is not None:
            refresh_token = search.group(0)[14:]

        elif search is None:
            LOGGER.debug('Could not find refresh_token from given url.')
            exit(1)

        # Searching for access_token
        search = re.search('access_token=\w+', redirected_link)

        if search is not None:
            access_token = search.group(0)[13:]

        elif search is None:
            LOGGER.debug('Could not find refresh_token from given url.')
            exit(1)

        return refresh_token, access_token

    def authenticate(self):

        if self.refresh_token is not None:
            return

        # Load config.json as json object
        configuration = json.load(open(CONFIG_LOCATION, 'r'))

        # Communicating to user
        auth_url = AUTHORIZATION_URL.format(CLIENT_ID=configuration['client_id'],
                                            RESPONSE_TYPE='token')

        LOGGER.info(
            '(Imgur-To-Folder does NOT collect any username or password data)')
        LOGGER.info('To authenticate, please go to specified URL and log-in:')
        LOGGER.info(auth_url)
        LOGGER.info(
            "After logging in you will be redirected to Imgur's front page.")

        redirected_link = str(input("\nPaste the redirected url given, here:"))

        # Authenicate
        refresh_token, access_token = self.parsing_redirected_link(
            redirected_link)

        # Read config.py
        configuration['refresh_token'] = refresh_token
        configuration['access_token'] = access_token

        # Write it back into the file
        with open(CONFIG_LOCATION, 'w') as config_file:
            json.dump(configuration, config_file, sort_keys=True, indent=4,)

        self.refresh_token = refresh_token

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

    def return_all_favorites(self, username, oldest=False):
        # Determine how favorites are sorted
        if oldest == True:
            favsort = 'oldest'
        else:
            favsort = 'newest'

        # Get configuration
        configuration = json.load(open(CONFIG_LOCATION))

        # Apply configuration to header and url
        headers = {'authorization': 'Bearer {token}'.format(
            token=configuration['access_token'])}

        number_of_favorites = 1
        page_number = 0
        list_of_all_links = []
        while number_of_favorites > 0:
            url = ACCOUNT_FAVORITES_URL.format(username=username,
                                               page_number=page_number,
                                               favoritesSort=favsort)
            req = requests.get(url, headers=headers)

            data = json.loads(req.text)['data']

            if 'error' in data:
                break
            elif data is None:
                continue

            number_of_favorites = len(data)

            for item in data:

                list_of_all_links.append(item['link'])

            page_number += 1

        return list_of_all_links

    def list_favorites_pages(self, username):

        # Get list of favorites from specified user
        favorites = self.return_all_favorites(username)

        LOGGER.info('Found %d favorites' % len(favorites))

        for link_count, link in enumerate(favorites):
            if link_count % 60 == 0:
                LOGGER.info('--------- [PAGE %d] ---------',
                            (link_count / 60) + 1)
            LOGGER.info(link)

    def download_favorites(self, username, oldest=False):
        """ Download all favorites within username. Each 'Page' will be 60 favorites """

        # Get list of favorites from specified user
        favorites = self.return_all_favorites(username, oldest)

        if self.max_favorites != None:
            favorites = favorites[:self.max_favorites]

        # Display the length of favorites
        LOGGER.info('Found %d favorites' % len(favorites))

        # Wait one second
        sleep(1)

        # For each link in favorites, download them.
        # link_count is the position of the current link in the list.
        for link_count, link in enumerate(favorites):
            # if current position is divisable by 60, then increase the page number
            if link_count % 60 == 0:
                LOGGER.info('--------- [PAGE %d] ---------',
                            (link_count / 60) + 1)
            self.detect_automatically(link)

            if self.max_favorites == link_count + 1:
                return

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

        # Create File Name

        """ Link names """
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

        """ Directory Name """
        # If directory_name is given, make it the new folder name
        if directory_name is not None:

            if len(directory_name) > MAX_NAME_LENGTH:
                directory_name = directory_name[:MAX_NAME_LENGTH]

            directory_name = self.replace_characters(directory_name)
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

        # If directory exists and user does not want to overwrite, skip
        elif os.path.exists(directory_name + link_name) and not self.overwrite:
            LOGGER.info('\tSkipping: ' + directory_name + link_name)
            return

        # Make GET request
        req = requests.get(url, stream=True)
        LOGGER.debug("Request: %s %s %s",
                     req.request.method,
                     req.request.url,
                     req.request.body)

        if req.status_code == 200:

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

    def change_desired_folder_path(self, folder_path):
        self.desired_folder_path = self.check_folder_path(folder_path)

        """
        If directory not given then get the absolute path.
        This is done since I had problems using relative paths during testing.
        Needed to make sure it was given a absolute path.
        """
        if self.desired_folder_path == '.' or self.desired_folder_path == './':
            absolute_path = self.check_folder_path(os.getcwd())
            self.desired_folder_path = absolute_path

        self.check_if_folder_exists()
