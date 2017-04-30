# Python modules
import argparse

# Dev defined modules
import config
from downloader import *

def parse_arguments():
    parser = argparse.ArgumentParser(description='Download images off Imgur to a folder of your choice!')
    parser.add_argument('urls', metavar = 'URLS', type = str, nargs = '*', help = 'Automatically detect urls')
    parser.add_argument('--folder', '-f', metavar = 'FOLDER_PATH', type = str, nargs = '?', help = 'Change desired folder path')
    parser.add_argument('--album', '-a', metavar = 'ALBUM_URL', type = str, nargs = '+', help = 'Download desired album to folder')
    parser.add_argument('--image', '-i', metavar = 'IMAGE_URL', type = str, nargs = '+', help = 'Download desired image to folder')
    parser.add_argument('--download-all-favorites', '-df', metavar = 'USERNAME', type = str, nargs = '?', help = 'Download all favorited images to folder')

    return parser.parse_args()

def main():
    args = parse_arguments()


    downloader = Downloader(client_id     = config.Client_ID,
                            client_secret = config.Client_Secret,
                            folder_path   = config.Desired_Folder_Path,
                            refresh_token = config.Refresh_Token)



    if (args.folder != None):

        downloader.change_folder(args.folder)

    if args.urls != None:
        for url in args.urls:
            downloader.detect_automatically(url)

    if (args.image != None):
        print ('Downloading single image to:', downloader.desired_folder_path)
        for image in args.image:
            print ('Downloading single image:', str(image))
            downloader.download_image(image)

    if (args.album != None):
        print ('Downloading album(s) to:', downloader.desired_folder_path)
        for album in args.album:
            ID = downloader.parse_for_gallery_id(album)
            downloader.download_album(ID)

    if (args.download_all_favorites != None):
        if not downloader.is_authenticated:
            downloader.authenticate()

        print ('Downloading Favorites to:', downloader.desired_folder_path)
        downloader.download_all_favorites(args.download_all_favorites)

    print('Done.')

if __name__ == '__main__':
    main()
