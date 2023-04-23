from imgurtofolder.api import ImgurAPI
from logging import getLogger

logger = getLogger('imgur')


class Imgur:
    def __init__(self, configuration):
        logger.debug('Configuration set')
        self._configuration = configuration
        self._api = ImgurAPI(configuration)

    def get_account_images(self, username, page=0):
        """
        Get all images from an account

        Parameters:
            username (str): The username of the account
            page (int): The page number to start on

        Returns:
            list: A list of all images from the account
        """

        _next_page = lambda _username, _page: self._api.get(
            f'account/{_username}/images/{_page}',
            {
                'Authorization': 'Bearer %s' % self._configuration.access_token,
            }
        )

        account_images = []

        while len(response := _next_page(username, page)) != 0:
            logger.info(f'Getting page {page} of account images')
            for item in response:
                account_images.append(item)
            response = _next_page(username, page)
            page += 1

        return account_images

    def get_gallery_favorites(self, username, sort='newest'):
        """
        Get all gallery favorites from an account

        Parameters:
            username (str): The username of the account
            sort (str): The sort order of the gallery favorites

        Returns:
            list: A list of all gallery favorites from the account
        """
        return self._api.get(
            f'account/{username}/gallery_favorites/{sort}',
            {
                'Authorization': 'Client-ID %s' % self._configuration.get_client_id()
            }
        )

