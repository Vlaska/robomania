from urllib.parse import urljoin

from robomania.config import settings


def get_asset_url(name: str, asset_type: str) -> str:
    return urljoin(str(settings.assets_base_url), f"{asset_type}s/{name}")
