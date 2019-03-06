# Derek Santos
# Python modules
import argparse

# Dev defined modules
from imgur_downloader import *

def parse_arguments():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(
        description='Download images off Imgur to a folder of your choice!')
    parser.add_argument('urls', metavar='URLS', type=str,
                        nargs='*', help='Automatically detect urls')
    parser.add_argument('--folder', '-f', metavar='FOLDER_PATH',
                        type=str, help='Change desired folder path')
    parser.add_argument('--download-latest-favorites', '-df', metavar='USERNAME',
                        type=str, nargs='?', help='Download latest favorited images to folder')
    parser.add_argument('--download-oldest-favorites', '-do', metavar='USERNAME',
                        type=str, nargs='?', help='Download oldest favorited images to folder')
    parser.add_argument('--download-account-images', '-dai', action='store_true',
                        help='Download latest favorited images to folder')
    parser.add_argument('--max-favorites', metavar='NUMBER_OF_MAX',
                        type=int,  help='Specify the max number of favorites to download')
    parser.add_argument('--page-start', metavar='STARTING_PAGE', default = 0,
                        type=int,  help='Specify the starting page number for fravorites')
    parser.add_argument('--list-all-favorites', '-lf', metavar='USERNAME',
                        type=str, nargs='?', help='List all favorites of a specified user')
    parser.add_argument('--overwrite', action='store_true',
                        help='Write over existing content. (Disables skipping.)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enables debugging output.')

    return parser.parse_args()


def main():
    args = parse_arguments()

    downloader = Imgur_Downloader(client_id=CONFIGURATION['client_id'],
                                  client_secret=CONFIGURATION['client_secret'],
                                  refresh_token=CONFIGURATION['refresh_token'],
                                  overwrite=args.overwrite,
                                  verbose=args.verbose,
                                  max_favorites=args.max_favorites)

    if args.folder is not None:
        CONFIGURATION['download_folder_path']  = args.folder

    if args.urls is not None:
        for url in args.urls:
            content = downloader.parse_url_by_content(url)
            downloader.download_by_type (*content, url)

    if args.download_latest_favorites is not None:
        if downloader.refresh_token == "":
            downloader.authenticate()

        LOGGER.info('Downloading Latest Favorites to: ' +
                    CONFIGURATION['download_folder_path'])

        downloader.download_favorites(args.download_latest_favorites,
                                      args.page_start,
                                      oldest=False)

    elif args.download_oldest_favorites is not None:

        if downloader.refresh_token == "":
            downloader.authenticate()

        LOGGER.info('Downloading Oldest Favorites to: ' +
                    CONFIGURATION['download_folder_path'])

        downloader.download_favorites(args.download_oldest_favorites,
                                      args.page_start,
                                      oldest=True)

    if args.list_all_favorites is not None:
        if downloader.refresh_token == "":
            downloader.authenticate()

        downloader.list_favorites_pages(args.list_all_favorites)

    if args.download_account_images is True:
        if downloader.refresh_token == "":
            downloader.authenticate()

        downloader.download_account_images()

    LOGGER.info('Done.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.info('User Interupted! (KeyboardInterrupt)')
    except Exception as e:
        LOGGER.info(e)
