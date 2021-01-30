from imgurtofolder.configuration import Configuration
from imgurtofolder.imgur import Imgur
from os import makedirs
from os.path import exists, expanduser, join, isfile, dirname
import json
import pytest

CONFIG_PATH = join(expanduser('~'), ".config", "imgurToFolder", 'config.json')


@pytest.fixture
def imgur():
    """Pytest fixture to yield an Imgur object"""
    if not exists(CONFIG_PATH):
        makedirs(dirname(CONFIG_PATH), exist_ok=True)

        with open(CONFIG_PATH, 'w') as current_file:
            current_file.write(json.dumps(dict(
                access_token="",
                client_id="",
                client_secret="",
                download_path="",
                refresh_token="")))

    with open(CONFIG_PATH, 'r') as current_file:
        data = json.loads(current_file.read())

        configuration = Configuration(
            config_path=CONFIG_PATH,
            access_token=data['access_token'],
            client_id=data['client_id'],
            client_secret=data['client_secret'],
            download_path=data['download_path'],
            refresh_token=data['refresh_token'],
            overwrite=False
        )
    imgur = Imgur(configuration)
    yield imgur


@pytest.mark.skip("Skipping to not pause tests... Should work.")
def test_authorize(imgur):

    imgur.authorize()
    assert imgur._configuration.get_access_token()
    assert imgur._configuration.get_refresh_token()
    with open(CONFIG_PATH, 'r') as current_file:
        data = json.loads(current_file.read())
        assert data['access_token']
        assert data['refresh_token']

@pytest.mark.skip("Not implemented and there might be a limit to how many access_tokens we can get")
def test_generate_access_token(imgur): 
    pass 

def test_get_account_images(imgur):
    """Test retrival of account images."""
    account_images = imgur.get_account_images("me", page=0)
    assert len(account_images) > 1


def test_get_gallery_favorites(imgur):
    account_gallery_favorites = imgur.get_gallery_favorites("me",
                                                            sort="newest")
    assert len(account_gallery_favorites) > 1

    account_gallery_favorites = imgur.get_gallery_favorites("me",
                                                            sort="oldest")
    assert len(account_gallery_favorites) > 1


@pytest.mark.skip("Skipping to not pause tests... Should work.")
def test_get_account_favorites(imgur):
    account_gallery_favorites = imgur.get_account_favorites("me",
                                                            sort="newest")
    assert len(account_gallery_favorites) > 1

    account_gallery_favorites = imgur.get_account_favorites("me",
                                                            sort="oldest")
    assert len(account_gallery_favorites) > 1


def test_get_account_submissions(imgur):
    assert False

def test_get_album(imgur):
    assert False
    
def test_get_gallery_album(imgur):
    assert False

def test_get_subreddit_gallery(imgur):
    assert False

def test_get_subreddit_image(imgur):
    assert False


def test_get_tag(imgur):

    total_images = imgur.get_tag('programming',
                                 sort='top',
                                 window='all',
                                 page=0,
                                 max_items=10)

    assert len(total_images) == 10

    total_images = imgur.get_tag('programming',
                                 sort='time',
                                 window='day',
                                 page=0,
                                 max_items=11)

    assert len(total_images) == 11

    total_images = imgur.get_tag('programming',
                                 sort='time',
                                 window='week',
                                 page=0,
                                 max_items=12)

    assert len(total_images) == 12

    total_images = imgur.get_tag('programming',
                                 sort='time',
                                 window='month',
                                 page=0,
                                 max_items=13)

    assert len(total_images) == 13

    total_images = imgur.get_tag('programming',
                                 sort='time',
                                 window='year',
                                 page=0,
                                 max_items=15)

    assert len(total_images) == 15
