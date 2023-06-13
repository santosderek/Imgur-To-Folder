from random import randint
from typing import Dict
from uuid import uuid4


def generate_hash() -> str:
    """
    Generate a random hash.
    """
    return ''.join(
        chr(randint(65, 90)) for _ in range(randint(5, 10))
    )


def generate_item(**kwargs) -> Dict:
    """
    Generate a random item as expected from an Imgur response.

    Parameters:
        `kwargs`: Optional arguments to override the default values.
    """

    _id: str = str(uuid4())

    return {
        'id': _id,
        'title': str(uuid4()),
        'description': None,
        'datetime': 1684204127,
        'cover': 'uVCJdgB',
        'cover_width': randint(16, 800),
        'cover_height': randint(16, 800),
        'account_url': generate_hash(),
        'account_id': randint(0, 1_000_000),
        'privacy': 'hidden',
        'layout': 'blog',
        'views': randint(0, 1_000_000),
        'link': f'https://imgur.com/a/{_id}',
        'ups': randint(0, 1_000_000),
        'downs': randint(0, 1_000_000),
        'points': randint(0, 1_000_000),
        'score': randint(0, 1_000_000),
        'is_album': True,
        'vote': None,
        'favorite': False,
        'nsfw': False,
        'section': '',
        'comment_count': randint(0, 1_000_000),
        'favorite_count': randint(0, 1_000_000),
        'topic': None,
        'topic_id': None,
        'images_count': randint(0, 5),
        'in_gallery': True,
        'is_ad': False,
        'tags': [],
        'ad_config': {
            'safeFlags': [
                'album',
                'in_gallery',
                'sixth_mod_safe',
                'gallery'
            ],
            'highRiskFlags': [],
            'unsafeFlags': [],
            'wallUnsafeFlags': [],
            'showsAds': True,
            'showAdLevel': 2,
            'safe_flags': [
                'album',
                'in_gallery',
                'sixth_mod_safe',
                'gallery'
            ],
            'high_risk_flags': [],
            'unsafe_flags': [],
            'wall_unsafe_flags': [],
            'show_ads': True,
            'show_ad_level': 2,
            'nsfw_score': 0,
            **kwargs
        }
    }
