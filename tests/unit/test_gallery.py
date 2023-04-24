from imgurtofolder.objects import Gallery
from unittest.mock import patch


@patch('imgurtofolder.objects.ImgurAPI')
def test_get_gallery_metadata(mock_imgur_api):

    mock_imgur_api.get.return_value = {
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
    }

    image_metadata = Gallery('12345678', mock_imgur_api).get_metadata()

    assert image_metadata.get('images') == [
        {
            'id': '1',
            'title': 'test',
            'link': 'https://i.imgur.com/12345678.jpg',
            'type': 'image/jpeg',
        }
    ]
    
