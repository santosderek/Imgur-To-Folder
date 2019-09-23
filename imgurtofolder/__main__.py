# Derek Santos
import argparse
import configuration
import imgur
import imgur_downloader
import json
import logs
from os.path import expanduser, exists, join
from sys import platform

log = logs.Log('main')

def parse_arguments():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(description='Download images off Imgur to a folder of your choice!')
    parser.add_argument('urls', metavar='URLS', type=str,
                        nargs='*', help='Automatically detect urls')

    parser.add_argument('--folder', '-f', metavar='FOLDER_PATH',
                        type=str, help='Change desired folder path')

    parser.add_argument('--download-latest-favorites', '-df', metavar='USERNAME',
                        type=str, help='Download latest favorited images to folder')

    parser.add_argument('--download-oldest-favorites', '-do', metavar='USERNAME',
                        type=str, help='Download oldest favorited images to folder')

    parser.add_argument('--download-account-images', '-dai', metavar='USERNAME',
                        type=str, help='Download account images to folder')

    parser.add_argument('--max-downloads', metavar='NUMBER_OF_MAX', default=50,
                        type=int,  help='Specify the max number of favorites to download')

    parser.add_argument('--page-start', metavar='STARTING_PAGE', default = 0,
                        type=int,  help='Specify the starting page number for fravorites')

    parser.add_argument('--list-all-favorites', '-lf', metavar='USERNAME',
                        type=str, help='List all favorites of a specified user')

    parser.add_argument('--overwrite', action='store_true',
                        help='Write over existing content. (Disables skipping.)')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enables debugging output.')

    return parser.parse_args()


def create_config():
    log.info('First time setup!')
    client_id = str(input('Paste your client id: '))
    client_secret = str(input('Paste your client secret: '))
    download_path = str(input('Paste your download path: '))
    return {'client_id' : client_id,
            'client_secret' : client_secret,
            'download_path' : download_path}

def main():
    log.debug('Parsing logs')
    args = parse_arguments()

    log.debug('Checking configuation')
    config_path = join(expanduser('~'), '.imgurToFolder', 'config.json')
    if exists(config_path):
        log.debug('Configuation Found!')
        with open(config_path, 'r') as current_file:
            data = json.load(current_file)
        config = configuration.Configuration(config_path   = config_path,
                                                    access_token  = data['access_token'],
                                                    client_id     = data['client_id'],
                                                    client_secret = data['client_secret'],
                                                    download_path = data['download_path'],
                                                    refresh_token = data['refresh_token'],
                                                    overwrite     = args.overwrite)

    else:
        log.debug('No configuation found!')
        result_config = create_config()
        config = configuration.Configuration(config_path   = config_path,
                                                    client_id     = result_config['client_id'],
                                                    client_secret = result_config['client_secret'],
                                                    download_path = result_config['download_path'],
                                                    overwrite     = args.overwrite)
        config.save_configuration()


    log.debug('Reacting to args')
    if args.folder is not None:
        config.set_download_path(args.folder)


    if args.verbose:
        log.set_debug()
        imgur.log.set_debug()
        imgur_downloader.log.set_debug()
        configuration.log.set_debug()

    log.debug('Setting Imgur class')
    imgur_class = imgur.Imgur(config)

    log.debug('Setting Imgur Downloader Class')
    downloader = imgur_downloader.Imgur_Downloader(imgur_class)

    log.debug('Imgur Downloader parse id')
    for item in args.urls:
        try:
            downloader.parse_id(item,
                                page=args.page_start,
                                max_items=args.max_downloads)

            if args.download_latest_favorites is not None:
                downloader.download_favorites(args.download_latest_favorites,
                                              page=args.page_start,
                                              max_items=args.max_downloads)

            if args.download_oldest_favorites is not None:
                downloader.download_favorites(args.download_oldest_favorites,
                                              latest=False,
                                              page=args.page_start,
                                              max_items=args.max_downloads)

            if args.list_all_favorites is not None:
                downloader.list_favorites(args.list_all_favorites,
                                          latest=True,
                                          page=args.page_start,
                                          max_items=args.max_downloads)

            if args.download_account_images is not None:
                downloader.download_account_images(args.download_account_images,
                                                   page=args.page_start,
                                                   max_items=args.max_downloads)
        except Exception as e:
            log.info('Error! %s' % e)

    log.info('Done.')


if __name__ == '__main__':
    main()

    # try:
    #     main()
    # except KeyboardInterrupt:
    #     log.info('User Interupted! (KeyboardInterrupt)')
    # except Exception as e:
    #     log.info(e)
