from unittest.mock import patch

import pytest

from imgurtofolder.objects import Gallery
from tests.awaitables import cast_as_awaitable


@pytest.mark.asyncio
@patch('imgurtofolder.objects.ImgurAPI')
async def test_get_gallery_metadata(mock_imgur_api):

    mock_imgur_api.get.return_value = cast_as_awaitable({
        'data': {
            'images': [
                {
                    'id': '1',
                    'title': 'test',
                    'link': 'https://i.imgur.com/12345678.jpg',
                    'type': 'image/jpeg',
                }
            ]
        }
    })

    image_metadata = await Gallery('12345678', mock_imgur_api).get_metadata()

    assert image_metadata.get('images') == [
        {
            'id': '1',
            'title': 'test',
            'link': 'https://i.imgur.com/12345678.jpg',
            'type': 'image/jpeg',
        }
    ]
