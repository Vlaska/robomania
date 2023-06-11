from __future__ import annotations

import logging
from typing import TypeAlias

from pydantic import BaseModel, Extra

logger = logging.getLogger("robomania.types")


class FacebookSubpost(BaseModel, extra=Extra.allow):
    text: str
    images: list[str]
    author: str
    timestamp: int
    publish_date: str


class FacebookPostScraped(BaseModel):
    post_id: str
    timestamp: int
    publish_date: str
    images: list[str]
    scrambled_url: str
    url: str
    text: str
    was_posted: bool
    subpost: FacebookSubpost | None = None


FacebookPosts: TypeAlias = list[FacebookPostScraped]
