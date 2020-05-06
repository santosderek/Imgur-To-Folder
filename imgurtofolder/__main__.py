# Derek Santos
import argparse
import configuration
import imgur
import imgur_downloader
import json
import logs
from os.path import expanduser, exists, join
from sys import platform
from traceback import print_exc

CONFIG_FOLDER_PATH = expanduser('~/.config/imgurToFolder')
CONFIG_FILE_NAME = 'config.json'

CONFIG_PATH = join(CONFIG_FOLDER_PATH, CONFIG_FILE_NAME)

log = logs.Log('main')

def parse_arguments():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(description='Download images off Imgur to a folder of your choice!')
    parser.add_argument('urls', metavar='URLS', type=str,
                        nargs='*', help='Automatically detect urls')

    parser.add_argument('--folder', '-f', metavar='PATH',
                        type=str, help='Change desired folder path')

    parser.add_argument('--change-default-folder', metavar='PATH',
                        type=str, help='Change the default desired folder path')

    parser.add_argument('--download-favorites', '-df', type=str, metavar='USERNAME',
                        help="Username to download favorites of. Default: latest")

    parser.add_argument('--oldest', action='store_true',
                        help="Sort favorites by oldest.")

    parser.add_argument('--download-account-images', '-dai', metavar='USERNAME',
                        type=str, help='Download account images to folder')

    parser.add_argument('--max-downloads', metavar='NUMBER_OF_MAX',
                        type=int,  help='Specify the max number of favorites to download')

    parser.add_argument('--start-page', metavar='STARTING_PAGE', default = 0,
                        type=int,  help='Specify the starting page number for fravorites')

    parser.add_argument('--list-all-favorites', '-lf', metavar='USERNAME',
                        type=str, help='List all favorites of a specified user')

    parser.add_argument('--print-download-path', action='store_true',
                        help='Print default download path.')

    parser.add_argument('--overwrite', action='store_true',
                        help='Write over existing content. (Disables skipping.)')

    parser.add_argument('--sort', choices=['time', 'top'], default='time',
                        help='How to sort subreddit time duration.')

    parser.add_argument('--window', choices=['day', 'week', 'month', 'year', 'all'], default='day',
                        help='Window of time for the sort method when using subreddit links. (Append "--sort top")')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enables debugging output.')

    return parser.parse_args()


def create_config():
    log.info('First time setup!')

    client_id = ""
    client_secret = ""
    download_path = ""

    while not client_id:
        try:
            client_id = str(input('Paste your client id: '))
        except Exception as e:
            log.debug("Error when getting client_id input", exc_info=True)

    while not client_secret:
        try:
            client_secret = str(input('Paste your client secret: '))
        except Exception as e:
            log.debug("Error when getting client_secret input", exc_info=True)

    while not download_path:
        try:
            download_path = str(input('Paste your download path: '))
            download_path = expanduser(download_path)
        except Exception as e:
            log.debug("Error when getting download_path input", exc_info=True)

    return {'client_id' : client_id,
            'client_secret' : client_secret,
            'download_path' : download_path}

def main():
    log.debug('Parsing logs')
    args = parse_arguments()

    log.debug('Checking configuation')
    if exists(CONFIG_PATH):
        log.debug('Configuation Found!')

        with open(CONFIG_PATH, 'r') as current_file:
            data = json.load(current_file)

        config = configuration.Configuration(config_path   = CONFIG_PATH,
                                             access_token  = data['access_token'],
                                             client_id     = data['client_id'],
                                             client_secret = data['client_secret'],
                                             download_path = data['download_path'],
                                             refresh_token = data['refresh_token'],
                                             overwrite     = args.overwrite)

    else:
        log.debug('No configuation found!')
        result_config = create_config()
        config = configuration.Configuration(config_path   = CONFIG_PATH,
                                             client_id     = result_config['client_id'],
                                             client_secret = result_config['client_secret'],
                                             download_path = result_config['download_path'],
                                             overwrite     = args.overwrite)
        config.save_configuration(True)


    log.debug('Reacting to args')


    if args.verbose:
        log.set_debug()
        imgur.log.set_debug()
        imgur_downloader.log.set_debug()
        configuration.log.set_debug()

    if args.print_download_path:
        log.info('Default download path: ' + config.get_download_path())

    downloader = imgur_downloader.Imgur_Downloader(config, args.max_downloads if args.max_downloads else 30)

    if args.folder is not None:
        downloader.set_download_path(expanduser(args.folder))

    if args.change_default_folder:
        downloader.set_default_folder_path(args.change_default_folder)

    if args.list_all_favorites is not None:
        downloader.list_favorites(args.list_all_favorites,
                                  latest=True,
                                  page=args.start_page,
                                  max_items=args.max_downloads if args.max_downloads else -1)


    log.debug('Parsing ids')
    for item in args.urls:
        try:
            downloader.parse_id(item,
                                page=args.start_page,
                                max_items=args.max_downloads if args.max_downloads else 30,
                                sort=args.sort,
                                window=args.window)
        except Exception as e:
            message = 'Error with url {}. Error Message: \n\n'.format(item)
            log.exception(message)


    if args.download_favorites is not None:
        log.debug('Downloading favorites by {}'.format("Oldest" if args.oldest else "Latest"))
        downloader.download_favorites(args.download_favorites,
                                      latest=not args.oldest,
                                      page=args.start_page,
                                      max_items=args.max_downloads if args.max_downloads else 30)



    if args.download_account_images is not None:
        log.debug('Downloading account images')
        downloader.download_account_images(args.download_account_images,
                                           page=args.start_page,
                                           max_items=args.max_downloads if args.max_downloads else 30)


    log.info('Done.')


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        log.info('User Interupted! (KeyboardInterrupt)')
    except Exception as e:
        log.info("Exception has occured", exc_info=True)
