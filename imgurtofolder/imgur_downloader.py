# Derek Santos
# 3rd party modules
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
BASE_URL_REGEX = r'(https?)?(://)?(www.)?(imgur.com)'

# Must be in format r'(/wordshere/)'
IMGUR_BASE_EXTENSIONS = {
'album' : [r'(/a/)'],
'gallery' : [r'(/g/)', r'(/gallery/)'],
'subreddit' : [r'(/r/)'],
'tag' : [r'(/t/)(\w+/)'],
'image' : [r'(/)(\w+)']
}

# Imgur's RESTful API Urls
IMGUR_API_URLS = {
'album' : { 'base'   : 'https://api.imgur.com/3/album/{albumHash}',
            'images' : 'https://api.imgur.com/3/album/{albumHash}/images',
            'image'  : 'https://api.imgur.com/3/album/{albumHash}/image/{imageHash}'},

'gallery' : {'base' : 'https://api.imgur.com/3/gallery/{section}',
             'full' : 'https://api.imgur.com/3/gallery/{section}/{sort}/{window}/{page}?showViral={showViral}&mature=true&album_previews={albumPreviews}'},

'subreddit' : {'subreddit' : 'https://api.imgur.com/3/gallery/r/{subreddit}/{sort}/{window}/{page}',
               'image' : 'https://api.imgur.com/3/gallery/r/{subreddit}/{subredditImageId}'},

'tag' : {'base':'https://api.imgur.com/3/gallery/t/{tagName}',
         'full' : 'https://api.imgur.com/3/gallery/t/{tagName}/{sort}/{window}/{page}'},

'image' : {'base': 'https://api.imgur.com/3/image/{imageHash}'}

}

# Create global configuration json variable
CONFIG_LOCATION = os.path.dirname(os.path.abspath(__file__)) + '/config.json'

# Load config json into memory
with open(CONFIG_LOCATION, 'r') as cfile:
    CONFIGURATION = json.load(cfile)

# Imgur API URLS
AUTHORIZATION_URL = 'https://api.imgur.com/oauth2/authorize?client_id=%s&response_type=token&state=authorizing'
ACCOUNT_FAVORITES_URL = 'https://api.imgur.com/3/account/{username}/favorites/{page_number}/{favoritesSort}'
ACCOUNT_IMAGES_URL = 'https://api.imgur.com/3/account/me/images/%d'



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
                 refresh_token="",
                 overwrite=False,
                 verbose=False,
                 max_favorites=None):

        if verbose:
            ENABLE_LOGGING_DEBUG()

        self.max_favorites = max_favorites

        # Storing refresh token
        self.refresh_token = refresh_token

        self.overwrite = overwrite

    def replace_characters(self, word):
        # NOTE: '\\/:*?"<>|.' are invalid folder characters in a file system
        invalid_characters = ['\\', "'", '/', ':',
                              '*', '?', '"', '<',
                              '>', '|', '.', '\n']

        for character in invalid_characters:
            word = word.replace(character, '')

        return word

    def parse_redirect_link(self, redirected_link):
        refresh_token = None
        access_token = None

        # Searching for refresh_token
        search = re.search(r'(refresh_token)\=(\w+)&', redirected_link)

        if search is not None:
            refresh_token = search.group(2)

        elif search is None:
            LOGGER.info('Could not find refresh token from given url.')
            exit(1)

        # Searching for access_token
        search = re.search('(access_token)\=(\w+)&', redirected_link)

        if search is not None:
            access_token = search.group(2)

        elif search is None:
            LOGGER.info('Could not find access token from given url.')
            exit(1)

        return refresh_token, access_token

    def authenticate(self):

        if not self.refresh_token == '':
            return

        global CONFIGURATION

        # Setting authorization url
        auth_url = AUTHORIZATION_URL % CONFIGURATION['client_id']

        # Messages
        login_message = \
        '(Imgur-To-Folder does NOT collect any username or password data)'
        '\nTo authenticate, please go to specified URL and log-in:'

        after_login_message = \
        "After logging in you will be redirected to Imgur's front page."

        # Alert User
        LOGGER.info(login_message)
        LOGGER.info(auth_url)
        LOGGER.info(after_login_message)

        # Parse redirected url
        redirected_link = str(input("\nPaste the redirected url given, here:"))
        refresh_token, access_token = self.parse_redirect_link(redirected_link)

        CONFIGURATION['refresh_token'] = refresh_token
        CONFIGURATION['access_token'] = access_token

        # Preserve last config
        # We only need to change refresh_token and access_token
        with open(CONFIG_LOCATION, 'r') as config_file:
            previous_config = json.load(config_file)
            previous_config['refresh_token'] = CONFIGURATION['refresh_token']
            previous_config['access_token'] = CONFIGURATION['access_token']

        # Write it back into the file
        with open(CONFIG_LOCATION, 'w') as config_file:
            json.dump(previous_config, config_file, sort_keys=True, indent=4,)

        self.refresh_token = refresh_token

    def return_account_images_by_number(self, page_number):
        # Set up bearer token for header
        bearer = 'Bearer %s' % CONFIGURATION['access_token']

        # Send get request
        response = requests.get(ACCOUNT_IMAGES_URL % int(page_number),
                                headers={'Authorization' : bearer})

        # Return response
        return json.loads(response.text)['data']

    def get_account_images(self, page_number=0):
        current_page = 0
        list_of_data = []


        item_list = self.return_account_images_by_number(current_page)
        while len(item_list) > 0:

            for item in item_list:
                list_of_data.append(item)

            current_page += 1
            item_list = self.return_account_images_by_number(current_page)

        return list_of_data

    def download_account_images(self):
        account_images = self.get_account_images()

        LOGGER.info('Downloading {} images'.format(len(account_images)))

        for item in account_images:
            if 'mp4' in item:
                content = self.parse_url_by_content(item['mp4'])
                self.download_by_type (*content, item['mp4'])

            elif 'link' in item:
                content = self.parse_url_by_content(item['link'])
                self.download_by_type (*content, item['link'])

    def return_favorites(self, username, oldest=False, starting_page = 0):
        # Determine how favorites are sorted
        if oldest == True:
            favsort = 'oldest'
        else:
            favsort = 'newest'

        # Apply CONFIGURATION to header and url
        bearer = 'Bearer %s' % CONFIGURATION['access_token']
        headers = {'Authorization' : bearer}

        number_of_favorites = 1
        page_number = starting_page
        list_of_all_links = []

        LOGGER.info('Retreving Favorites!')

        while number_of_favorites > 0:
            url = ACCOUNT_FAVORITES_URL.format(username=username,
                                               page_number=page_number,
                                               favoritesSort=favsort)
            req = requests.get(url, headers=headers)

            data = json.loads(req.text)['data']

            if 'error' in data:
                LOGGER.info ('ERROR! When returning favorites:')
                LOGGER.info (data)
                break
            elif data is None:
                continue

            number_of_favorites = len(data)

            for item in data:

                list_of_all_links.append(item['link'])

            if self.max_favorites and \
                len(list_of_all_links) >= self.max_favorites:

                break

            page_number += 1

        return list_of_all_links[:self.max_favorites]

    def list_favorites_pages(self, username):

        # Get list of favorites from specified user
        favorites = self.return_favorites(username)

        LOGGER.info('Found %d favorites' % len(favorites))

        for link_count, link in enumerate(favorites):
            if link_count % 60 == 0:
                LOGGER.info('--------- [PAGE %d] ---------',
                            (link_count / 60) + 1)
            LOGGER.info(link)

    def download_favorites(self, username, page_start = 0, oldest=False):
        """
            Download all favorites within username.
            Each 'Page' will be 60 favorites
        """

        # Get list of favorites from specified user
        favorites = self.return_favorites(username, oldest, page_start)

        if self.max_favorites != None:
            favorites = favorites[:self.max_favorites]

        # Display the length of favorites
        LOGGER.info('Found %d favorites' % len(favorites))

        # Wait 1/2 second
        sleep(.5)

        # For each link in favorites, download them.
        # link_count is the position of the current link in the list.
        for link_count, link in enumerate(favorites, page_start):
            # if current position is divisable by 60, then increase the page number
            if link_count % 60 == 0:
                LOGGER.info('--------- [PAGE %d] ---------',
                            link_count / 60)

            content = self.parse_url_by_content(link)
            self.download_by_type (*content, link)

            if self.max_favorites == link_count + 1:
                return

    def parse_id_by_type(self, url, type):

        id = ''
        for extension in IMGUR_BASE_EXTENSIONS[type]:
            id = re.sub(BASE_URL_REGEX + extension, '', url)

        return id

    def parse_url_by_content(self, url):
        """
        This function takes a url and runs regular expressions against it.
        Based on the regular expression that finds a match, the funciton will
        call `parse_id_by_type` and pass the url along with the type of url found.
        """

        id = ''

        for key in IMGUR_BASE_EXTENSIONS.keys():
            for extension in IMGUR_BASE_EXTENSIONS[key]:

                result = re.search(BASE_URL_REGEX + extension, url)

                if result and key == 'album':
                    id = self.parse_id_by_type(url, 'album')
                    LOGGER.debug('ID: %s', id)
                    return id, 'album'

                elif result and key == 'gallery':
                    id = self.parse_id_by_type(url, 'gallery')
                    LOGGER.debug('ID: %s', id)
                    return id, 'gallery'

                elif result and key == 'subreddit':
                    id = self.parse_id_by_type(url, 'subreddit')
                    LOGGER.debug('ID: %s', id)
                    return id, 'subreddit'

                elif result and key == 'tag':
                    id = self.parse_id_by_type(url, 'tag')
                    LOGGER.debug('ID: %s', id)
                    return id, 'tag'

                elif result and key == 'image':
                    id = result.group(6)
                    LOGGER.debug('ID: %s', id)
                    return id, 'image'

        return url, None

    def download(self, images, title, is_album = False):
        """Should take in a list to download. If a folder name is specified then
        download to default directory using folder_name.
        """
        # Max length of a file name [Windows]
        MAX_NAME_LENGTH = 65
        path = CONFIGURATION['download_folder_path']

        title = self.replace_characters(title)

        if len(title) > MAX_NAME_LENGTH:
            title = title[:MAX_NAME_LENGTH]

        if is_album:
            path = os.path.join(CONFIGURATION['download_folder_path'], title)

            if not os.path.exists(path):
                os.mkdir(path)

        for pos, image in enumerate(images):
            # Last resort (Edge Cases)
            if image[-4:] == 'gifv':
                image = image[:-1]

            extension = image[image.rfind('.'):]

            if is_album:
                filename = title + ' - ' + str(pos + 1) + extension
                download_path = os.path.join(path, filename)
                LOGGER.info('Downloading: ' + filename)

            else:
                filename = title + extension
                download_path = os.path.join(path, filename)
                LOGGER.info('Downloading: ' + title + extension)

            if os.path.exists(download_path) and not self.overwrite:
                LOGGER.info('\tSkipping: ' + download_path)
                continue

            req = requests.get(image, stream=True)
            if req.status_code == 200:

                # Number of bytes in a megabyte : float(1 << 20)
                file_size = int(req.headers.get('content-length', 0)) / \
                            float(1 << 20)

                LOGGER.info('\t%s, File Size: %.2f MB', filename, file_size )

                with open(download_path, 'wb') as image_file:
                    req.raw.decode_content = True
                    shutil.copyfileobj(req.raw, image_file)
            else:
                LOGGER.info('\tERROR! Can not download: ' + download_path)
                LOGGER.info('\tStatus code: ' + str(req.status_code))

    def download_by_type(self, id, type, url):
        header = {'Authorization': 'Client-ID %s' % CONFIGURATION['client_id']}
        links = []
        details = None

        if type == 'album':
            url = IMGUR_API_URLS['album']['base'].format(albumHash=id)
            req = requests.get(url, headers = header)
            details = json.loads(req.text)['data']

        elif type == 'gallery':
            url = IMGUR_API_URLS['gallery']['base'].format(section=id)
            req = requests.get(url, headers = header)
            details = json.loads(req.text)['data']

        elif type == 'subreddit':

            # Need subreddit
            result = re.search(r'(/r/)(\w+/)', url)[0].replace('/r/', '')
            subreddit = result[:-1]

            url = IMGUR_API_URLS['subreddit']['image'].format(subreddit = subreddit,
                                                              subredditImageId = id)
            req = requests.get(url, headers = header)
            details = json.loads(req.text)['data'][0]

        elif type == 'tag':
            # Use the ['gallery']['base'] url since there are
            # edge cases that don't work with ['tag']['base']
            url = IMGUR_API_URLS['gallery']['base'].format(section=id)
            req = requests.get(url, headers = header)
            details = json.loads(req.text)['data']

        elif type == 'image':
            url = IMGUR_API_URLS['image']['base'].format(imageHash = id)
            req = requests.get(url, headers = header)
            details = json.loads(req.text)['data']

        else:
            details = {'link' : url,
                       'title' : url[url.rfind('/')+1:url.rfind('.')]}

        # Find images
        if 'images' in details:
            for image in details['images']:
                # prefer mp4
                if 'mp4' in image:
                    links.append(image['mp4'])
                elif 'gif' in image:
                    links.append(image['gif'])
                else:
                    links.append(image['link'])

        elif 'link' in details:

            if 'mp4' in details:
                links.append(details['mp4'])
            elif 'gif' in details:
                links.append(details['gif'])
            else:
                links.append(details['link'])

        # Find title
        if not 'title' in details or details['title'] is None:
            title = str(id)

        elif type is not None:
            title = details['title'] + ' - ' + str(id)

        else:
            title = details['title']

        #Pass to download
        if type == 'album' or type == 'gallery' or type == 'tag':
            self.download (links, title, True)
        else:
            self.download (links, title)
