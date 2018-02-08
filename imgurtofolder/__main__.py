# Python modules
import argparse

# Dev defined modules
import json
from imgur_downloader import *


""" Constants """

# Get config.json file path
CONFIG_LOCATION = os.path.dirname(os.path.abspath(__file__)) + '/config.json'


configuration = json.load(open(CONFIG_LOCATION, 'r'))


def parse_arguments():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(
        description='Download images off Imgur to a folder of your choice!')
    parser.add_argument('urls', metavar='URLS', type=str,
                        nargs='*', help='Automatically detect urls')
    parser.add_argument('--folder', '-f', metavar='FOLDER_PATH',
                        type=str, help='Change desired folder path')
    parser.add_argument('--album', '-a', metavar='ALBUM_URL',
                        type=str, nargs='+', help='Download desired album to folder')
    parser.add_argument('--image', '-i', metavar='IMAGE_URL',
                        type=str, nargs='+', help='Download desired image to folder')
    parser.add_argument('--download-latest-favorites', '-df', metavar='USERNAME',
                        type=str, nargs='?', help='Download latest favorited images to folder')
    parser.add_argument('--download-oldest-favorites', '-do', metavar='USERNAME',
                        type=str, nargs='?', help='Download oldest favorited images to folder')
    parser.add_argument('--max-favorites', metavar='NUMBER_OF_MAX',
                        type=int,  help='Specify the max number of favorites to download')
    parser.add_argument('--list-all-favorites', '-lf', metavar='USERNAME',
                        type=str, nargs='?', help='List all favorites of a specified user')
    parser.add_argument('--overwrite', action='store_true',
                        help='Write over existing content. (Disables skipping.)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enables debugging output.')

    return parser.parse_args()


def main():
    args = parse_arguments()

    downloader = Imgur_Downloader(client_id=configuration['client_id'],
                                  client_secret=configuration['client_secret'],
                                  folder_path=configuration['download_folder_path'],
                                  refresh_token=configuration['refresh_token'],
                                  single_images_folder=configuration['single_images_folder'],
                                  overwrite=args.overwrite,
                                  verbose=args.verbose,
                                  max_favorites=args.max_favorites)

    if args.folder is not None:
        downloader.change_desired_folder_path(args.folder)

    if args.urls is not None:
        for url in args.urls:
            downloader.detect_automatically(url)

    if args.image is not None:
        LOGGER.info('Downloading single image to: ' +
                    downloader.desired_folder_path)
        for image in args.image:
            LOGGER.info('Downloading single image: ' + str(image))
            downloader.download_image(image)

    if args.album is not None:
        LOGGER.info('Downloading album(s) to: ' +
                    downloader.desired_folder_path)
        for album in args.album:
            ID = downloader.parse_for_gallery_id(album)
            downloader.download_album(ID)

    if args.download_latest_favorites is not None or args.download_oldest_favorites is not None:
        if not downloader.is_authenticated:
            downloader.authenticate()

        LOGGER.info('Downloading Favorites to: ' +
                    downloader.desired_folder_path)

        if args.download_latest_favorites is not None:
            downloader.download_favorites(args.download_latest_favorites,
                                          oldest=False)

        elif args.download_oldest_favorites is not None:
            downloader.download_favorites(args.download_oldest_favorites,
                                          oldest=True)

    if args.list_all_favorites is not None:
        if not downloader.is_authenticated:
            downloader.authenticate()

        downloader.list_favorites_pages(args.list_all_favorites)

    LOGGER.info('Done.')


if __name__ == '__main__':
    main()
