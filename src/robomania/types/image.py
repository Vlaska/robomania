from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Generator
from urllib.parse import urlparse

import aiohttp
import disnake
from PIL import Image as PILImage

from robomania.utils import rewindable_buffer

logger = logging.getLogger('robomania.types')
MAX_IMAGES_PER_MESSAGE = 10
MAX_TOTAL_SIZE_OF_IMAGES = 8 * 1024 * 1024


class Image:
    _data: io.BytesIO
    image: io.BytesIO
    DOWNSAMPLE_IMAGE_RESOLUTION_BY = [3 / 4, 1 / 2, 1 / 4, 1 / 8, 1 / 16]

    def __init__(self, data: io.BytesIO, name: str) -> None:
        self._data = data
        self.name = name
        self.image = data

    def _change_image_format(self) -> None:
        self.image = io.BytesIO()

        with rewindable_buffer(self._data, self.image) as (data, image):
            img = PILImage.open(data)
            img.convert('RGB').save(image, 'jpeg')

    def _reduce_image_resolution(self, factor: float) -> None:
        self.image = io.BytesIO()

        with rewindable_buffer(self._data, self.image) as (data, image):
            img = PILImage.open(data)
            old_x, old_y = img.size
            new_size = (int(old_x * factor), int(old_y * factor))
            resized_img = img.resize(new_size)
            resized_img.save(image, 'jpeg')

    def reduce_size(self, max_size: int) -> None:
        self._change_image_format()

        if self.size <= max_size:
            return

        for factor in self.DOWNSAMPLE_IMAGE_RESOLUTION_BY:
            self._reduce_image_resolution(factor)

            if self.size <= max_size:
                break
        else:
            raise ValueError(
                'Could not reduce image size below given size constraint.'
            )

    @property
    def size(self) -> int:
        return self.image.getbuffer().nbytes

    @property
    def file(self) -> disnake.File:
        return disnake.File(self.image, self.name)

    @staticmethod
    def prepare_images(
        images: list[Image]
    ) -> Generator[list[disnake.File], None, None]:
        current_image_group: list[disnake.File] = []
        current_total_size = 0

        try:
            while True:
                image = images.pop(0)

                if image.size > MAX_TOTAL_SIZE_OF_IMAGES:
                    logger.info('Image too big, trying to reduce size.')
                    try:
                        image.reduce_size(MAX_TOTAL_SIZE_OF_IMAGES)
                    except ValueError:
                        logger.error('Image still too big, skipping.')
                        continue

                if (
                    len(current_image_group) + 1 > MAX_IMAGES_PER_MESSAGE or
                    image.size + current_total_size > MAX_TOTAL_SIZE_OF_IMAGES
                ):
                    yield current_image_group

                    current_image_group = []
                    current_total_size = 0

                current_total_size += image.size
                current_image_group.append(
                    disnake.File(image.image, image.name)
                )
        except IndexError:
            pass

        yield current_image_group

    @staticmethod
    async def download_images(
        images: list[str]
    ) -> list[Image]:
        out = []
        async with aiohttp.ClientSession() as session:
            for url in images:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.warning('Problem with image download.')
                        continue

                    data = io.BytesIO(await resp.read())
                    image_path = Path(urlparse(url).path)
                    out.append(Image(data, image_path.name))

        logger.debug(f'Downloaded {len(out)} images')
        return out
