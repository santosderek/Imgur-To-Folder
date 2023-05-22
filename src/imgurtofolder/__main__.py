import argparse
import asyncio
import json
from argparse import Namespace
from logging import getLogger
from os.path import expanduser, join
from pathlib import Path
from typing import Optional

from imgurtofolder.api import ImgurAPI, OAuth
from imgurtofolder.configuration import Configuration
from imgurtofolder.downloader import (download_account_images,
                                      download_favorites, download_urls)
from imgurtofolder.objects import Account

CONFIG_PATH = join(expanduser('~'), ".config", "imgurToFolder", 'config.json')

log = getLogger(__name__)


def parse_arguments():
    """ Parse command line arguments """
    parser = argparse.ArgumentParser(
        description='Download images off Imgur to a folder of your choice!')
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

    parser.add_argument('--max-downloads', metavar='NUMBER_OF_MAX', default=30,
                        type=int, help='Specify the max number of favorites to download')

    parser.add_argument('--start-page', metavar='STARTING_PAGE', default=0,
                        type=int, help='Specify the starting page number for fravorites')

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


def ask_for(name: str, expand: bool = True) -> str:
    """
    Ask for a value; mostly to reduce code duplication.

    Parameters:
        name (str): The name of the value.
        expand (bool): Expand the path.

    Returns:
        str: The value.
    """
    _result: Optional[str] = None

    while not _result:
        try:
            _result = str(input(f'Paste your {name}: '))

            if expand:
                _result = expanduser(_result)
        except Exception as e:
            log.debug(f"Error when getting {name}", exc_info=True)
    return _result


def return_config_dict():
    """
    Create a configuration file.
    """

    log.info('First time setup!')

    client_id = ask_for('client id')
    client_secret = ask_for('client secret')
    download_path = ask_for('download path', expand=True)

    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'download_path': download_path
    }


def load_config(path: str) -> dict:
    """
    Load a configuration file and create one if it doesn't exist.

    Parameters:
        path (str): The path to the configuration file.

    Returns:
        dict: The configuration file.
    """
    _path = Path(path)

    if not _path.exists():
        log.debug('Configuation not found!')
        return return_config_dict()

    try:
        log.debug('Configuation found!')
        with Path(path).open('r') as current_file:
            return json.load(current_file)
    except Exception as e:
        log.error("Error when loading config", exc_info=True)
        exit(1)  # TODO: Don't exit here and keep asking instead.


def main():
    log.debug('Parsing logs')
    args = parse_arguments()

    log.debug('Checking configuation')
    config = fetch_configuration(args)

    log.debug('Reacting to args')

    if args.verbose:
        # set root logger to debug
        getLogger().setLevel('DEBUG')

    if args.print_download_path:
        log.info(f'Default download path: {config.download_path}')

    if args.folder is not None:
        config.download_path = expanduser(args.folder)

    if args.change_default_folder:
        config.download_path = expanduser(args.change_default_folder)
        config.save()

    # Authorize if not already
    if not config.access_token:
        OAuth(config).authorize()

    api = ImgurAPI(config)

    if args.list_all_favorites is not None:
        asyncio.run(
            Account(
                username='me',
                api=api
            ).get_account_favorites('me')
        )

    asyncio.run(download_urls(args.urls, api))

    if args.download_favorites is not None:
        log.debug(
            f'Downloading favorites by {"Oldest" if args.oldest else "Latest" }'
        )
        download_favorites(
            args.download_favorites,
            sort='newest' if args.oldest else 'latest',
            page=args.start_page,
            max_items=args.max_downloads
        )

    if args.download_account_images is not None:
        log.debug('Downloading account images')
        download_account_images(
            args.download_account_images,
            page=args.start_page,
            max_items=args.max_downloads
        )

    log.info('Done.')


def fetch_configuration(args: Namespace) -> Configuration:
    _config_dict = load_config(CONFIG_PATH)
    config = Configuration(
        **{
            'config_path': CONFIG_PATH,
            **_config_dict,
            'overwrite': args.overwrite
        }
    )
    config.save(True)
    return config


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        log.info('User Interupted! (KeyboardInterrupt)')
    except Exception as e:
        log.info("Exception has occured", exc_info=True)
