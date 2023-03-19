from __future__ import annotations

import logging
from typing import TypeAlias

from pydantic import BaseModel

logger = logging.getLogger("robomania.types")


class FacebookPostScraped(BaseModel):
    post_id: str
    timestamp: int
    publish_date: str
    images: list[str]
    scrambled_url: str
    url: str
    text: str
    was_posted: bool


FacebookPosts: TypeAlias = list[FacebookPostScraped]
