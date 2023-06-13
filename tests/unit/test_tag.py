from random import randint
from typing import Dict
from unittest.mock import patch
from uuid import uuid4

import pytest

from imgurtofolder.objects import Tag
from tests.awaitables import cast_as_awaitable
from tests.generate import generate_hash, generate_item


def generate_tag(tag: str, number_of_items: int = 3) -> Dict:

    description: str = str(uuid4())
    return {
        'name': tag,
        'display_name': tag.capitalize(),
        'followers': randint(0, 1_000_000),
        'total_items': randint(0, 1_000_000),
        'following': False,
        'is_whitelisted': True,
        'background_hash': generate_hash(),
        'thumbnail_hash': None,
        'accent': f'{randint(1, 1_000_000)}',
        'background_is_animated': False,
        'thumbnail_is_animated': False,
        'is_promoted': False,
        'description': description,
        'logo_hash': None,
        'logo_destination_url': None,
        'description_annotations': {},
        'items': [generate_item() for _ in range(number_of_items)],
    }


@pytest.mark.asyncio
@patch('imgurtofolder.objects.ImgurAPI')
async def test_get_image_metadata(mock_imgur_api):

    _tag = generate_tag('test')

    mock_imgur_api.get.return_value = cast_as_awaitable({
        'data': _tag,
    })

    image_metadata = await Tag('12345678', mock_imgur_api).get_metadata()

    assert len(image_metadata['items']) == 3

    for key in _tag.keys():
        assert image_metadata[key] == _tag[key]
