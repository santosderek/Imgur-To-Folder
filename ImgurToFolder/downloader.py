#3rd party modules
import imgurpython as ip
import requests
# Python modules
import os
import shutil

# Dev defined modules
import config

class Downloader:
    def __init__(self, client_id, client_secret, folder_path, refresh_token = ''):
        if refresh_token == '' or refresh_token == None:
            self.client = ip.ImgurClient(client_id, client_secret)
        else:
            self.client = ip.ImgurClient(client_id, client_secret, refresh_token=refresh_token)

        self.desired_folder_path = self.check_folder_path(folder_path)
        self.refresh_token = refresh_token
        self.is_authenticated = False

        # If refresh_token was given, set true
        if self.refresh_token != '':
            self.is_authenticated = True


    def parse_for_gallery_id(self, url):

        # Base url path for gallery and album
        # If base url path ever changes only need to change these two variables
        album = 'imgur.com/a/'
        gallery = 'imgur.com/gallery/'

        # Must start as -1 as a 'NULL'
        start_position = -1

        if url.find(album) != -1:
            start_position = int( url.find(album) + len(album) )

        elif url.find(gallery) != -1:
            start_position = int( url.find(gallery) + len(gallery) )

        if start_position != -1:
            end_position = int (url.find('/', start_position) )
            if (end_position > -1):
                return url[start_position:end_position]
            else:
                return url[start_position:]
        else:
            return None

    def replace_characters(self, word):
        # NOTE: '\\/:*?"<>|.' are invalid folder characters in a file system
        invalid_characters = ['\\','\'','/',':','*','?','"','<','>','|','.']
        for character in invalid_characters:
            word = word.replace(character, '')

        return word

    def check_folder_path(self, path):
        """ Checks if the last char of the path has a '/' to complete the extension """
        path = path.replace('\\','/')

        if path[-1:] != '/':
            path += '/'
        return path

    def authenticate(self):

        if self.refresh_token != '' and self.refresh_token != None:
            return

        # Communicating to user
        pin_url = self.client.get_auth_url('pin')

        print ()
        print ('Please go to specified URL: (Imgur-To-Folder does NOT collect any username or password data)')
        print (pin_url)
        print ()

        pin = str(input('Plase type or paste the pin given here:'))

        # Authenicate
        credentials = self.client.authorize(pin, 'pin')
        self.client.set_user_auth(credentials['access_token'],
                                    credentials['refresh_token'])

        # Now save it in the config.py file

        # Get config.py file
        location = os.path.dirname(os.path.abspath(__file__))
        location = self.check_folder_path(location)
        location += 'config.py'

        # Read config.py
        with open(location,'r') as config_file:
            data = config_file.readlines()

        # Look for Refresh_Token line
        count = 0
        found_line_number = None
        for line in data:

            if line.find('Refresh_Token') != -1:
                found_line_number = count

            count += 1

        # Replace the line
        if found_line_number != None:
            line = 'Refresh_Token = \'%s\'' % credentials['refresh_token']
            line += '\n'
            data[found_line_number] = line

        # Write it back into the file
        with open(location,'w') as config_file:
            config_file.writelines(data)

    def detect_automatically(self, url = None):

        if url == '' or url == None:
            return

        elif (url.find('imgur.com/gallery/') != -1) or (url.find('imgur.com/a/') != -1):

            response = self.parse_for_gallery_id(url)

            if response == None:
                print ('ERROR: ID parsing failed for album / gallery url:', url)
                return

            self.download_album(response)

        else:
            print ('Downloading image: ', url, end='', flush=True)
            self.download_image(url)
            print (' - [FINISHED]')


    def download_all_favorites(self, username):

        favorites = self.client.get_account_favorites(username)

        for selection in favorites:

            ID = self.parse_for_gallery_id(selection.link)
            # If an album
            if ID != None:
                self.download_album(ID)
            # If an image
            else:
                print ('Downloading single image:', selection.link)
                self.download_image(selection.link)

    def download_album(self, ID = None):


        if ID == None:
            print ('ERROR: No album link given')
            return

        # Try to get album_title

        try:
            album_title = self.client.get_album(ID).title
        except ip.helpers.error.ImgurClientError:
            album_title = None

        if album_title == None:
            try:
                album_title = self.client.gallery_item(ID).title
            except ip.helpers.error.ImgurClientError:
                pass


            # Try to get album section, to use later
            try:
                section = self.client.get_album(ID).section
            except ip.helpers.error.ImgurClientError:
                section = None

            # Try to get gallery section if none was given earlier
            if section == None:
                try:
                    section = self.client.gallery_item(ID).section
                except ip.helpers.error.ImgurClientError:
                    section = None

            # If section was given at any point earlier use it to find the title
            # Else, make album_title == None
            if section != None:
                try:
                    album_title = self.client.subreddit_image(section, ID).title
                except ip.helpers.error.ImgurClientError:
                    album_title = None

        # If album_title still equals None, make the album title the ID
        if album_title == None:
            album_title = ID

        # Look for invalid characters
        album_title = self.replace_characters(album_title)

        # Alert the user
        print ('Downloading album:', album_title, end='', flush=True)

        # This is a bool incase the get_album function fails. If set to true,
        # the program will check if it was a gallery.
        check_if_gallery = False

        # Try to see if it is an album
        try:
            for position, image in enumerate (self.client.get_album(ID).images):
                self.download_image(image['link'], album_title, position + 1)

            print (' - [FINISHED]')


        except ip.helpers.error.ImgurClientError:
            check_if_gallery = True

        if (check_if_gallery):
            try:
                self.download_image ( self.client.gallery_item(ID).link, album_title )
                print (' - [FINISHED]')
            except ip.helpers.error.ImgurClientError as e:
                print ('\nERROR:', e)




    def download_image(self, url = '', directory_name = None, album_position = 0):

        # Length of a file name
        MAX_NAME_LENGTH = 65

        # changes .gifv links to .gif since imgur supports this transfer
        if url[-4:] == 'gifv':
            url = url[:-4] + 'gif'

        req = requests.get(url, stream = True)

        if req.status_code == 200:

            #Link names
            if album_position == 0:
                link_name = url[url.rfind('/') + 1:]

            else:
                # First erase invalid characters
                link_name = directory_name[:MAX_NAME_LENGTH] + ' - ' + str( album_position )
                link_name = self.replace_characters(link_name)

                # Then add file_extension
                file_extension = url[url.rfind('.'):]
                link_name += file_extension

            # If directory_name is given, make it the new folder name
            if directory_name != None:

                if len(directory_name) > MAX_NAME_LENGTH:
                    directory_name = directory_name[:MAX_NAME_LENGTH]

                directory_name = self.replace_characters(directory_name)

                # If directory not given then get the absolute path
                if self.desired_folder_path == '.' or './':
                    absolute_path = os.getcwd()
                    absolute_path = self.check_folder_path(absolute_path)
                    directory_name = absolute_path + directory_name
                else:
                    directory_name = self.desired_folder_path + directory_name

                directory_name = self.check_folder_path(directory_name)


            # Else make the desired_folder_path the folder to download in
            elif config.enable_single_images_folder:
                directory_name = self.desired_folder_path + 'Single-Images/'

            else:
                directory_name = self.desired_folder_path






            #if len(link_name) > MAX_NAME_LENGTH:
            #
            #    link_name = link_name[:MAX_NAME_LENGTH]
            # Check if directory exists

            if not os.path.exists(directory_name):
                os.makedirs(directory_name)




            with open(directory_name + link_name, 'wb') as image_file:
                req.raw.decode_content = True
                shutil.copyfileobj(req.raw, image_file)

            #with open(directory_name + link_name, 'wb') as image_file:
            #    for chunk in req:
            #        image_file.write(chunk)


    def change_folder(self, folder_path):
        self.desired_folder_path = self.check_folder_path(folder_path)
