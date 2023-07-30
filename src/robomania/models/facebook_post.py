from __future__ import annotations

import logging
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger("robomania.types")


class FacebookSubpost(BaseModel):
    text: str
    images: list[str]
    author: str
    timestamp: int
    publish_date: str

    model_config = ConfigDict(extra="allow")


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
