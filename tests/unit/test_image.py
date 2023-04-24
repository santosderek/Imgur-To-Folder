import asyncio
from imgurtofolder.api import ImgurAPI
from imgurtofolder.configuration import Configuration

from imgurtofolder.objects import Image
from unittest.mock import patch, Mock

import pytest


# @pytest.mark.asyncio
# @patch('imgurtofolder.api.ImgurAPI')
# async def test_download_image(mock_imgur_api):
#     # configuration = Configuration(
#     #     client_id='123',
#     #     client_secret='123',
#     #     download_path='~/Downloads',
#     #     config_path='~/.config/imgurtofolder/config.json',
#     #     access_token='123',
#     #     refresh_token='123',
#     # )
# 
#     response = Mock()
#     response.status_code = 200
#     response.json.return_value = {
#         'data': {
#             'id': '1',
#             'title': 'test',
#             'link': 'https://i.imgur.com/1.jpg',
#             'type': 'image/jpeg',
#         }
#     }
# 
#     mock_imgur_api.return_value.get.return_value = response
#     await Image('https://i.imgur.com/1.jpg', mock_imgur_api).download()


@patch('imgurtofolder.objects.ImgurAPI')
def test_get_image_metadata(mock_imgur_api):

    mock_imgur_api.get.return_value = {
        'data': {
            'id': '1',
            'title': 'test',
            'link': 'https://i.imgur.com/12345678.jpg',
            'type': 'image/jpeg',
        }
    }

    image_metadata = Image('12345678', mock_imgur_api).get_metadata()
    assert image_metadata['id'] == '1'
    assert image_metadata['title'] == 'test'
    assert image_metadata['link'] == 'https://i.imgur.com/12345678.jpg'
    assert image_metadata['type'] == 'image/jpeg'

