from urllib.parse import urljoin

from robomania.config import settings


def get_asset_url(name: str, type: str) -> str:
    return urljoin(settings.asset_base_url, f"{type}/{name}")
