from __future__ import annotations

from pathlib import Path

import pytesseract as tes
from disnake.ext import commands
from PIL import Image, ImageDraw, ImageOps

THRESHOLD = 1


class Planner:
    def process_img(self, img: Image.Image) -> Image.Image:
        grayscale = img.convert('L')
        inverted = ImageOps.invert(grayscale)
        threshold = inverted.point(
            lambda x: 255 if x > THRESHOLD else 0
        )
        high_contrast = threshold.convert('RGB')
        ImageDraw.Draw(high_contrast).rectangle(
            ((650, 0), (999, 200)),
            fill=(255, 255, 255)
        )
        return high_contrast

    def read_text_from_image(self, img: Image.Image) -> str:
        processed_img = self.process_img(img)

        return tes.image_to_string(processed_img, lang='pol')

    def is_plan_text(self, text: str) -> bool:
        return 'Tydzień w DOM EQ!' in text

    def process_text(self, text: str) -> list:
        pass

    @staticmethod
    def _open_image(path: Path):
        return Image.open(path)


class PlannerCog(commands.Cog, Planner):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
