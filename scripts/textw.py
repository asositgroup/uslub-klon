"""Matn enini haqiqiy shrift bilan o'lchash (brauzerda shrift yuklanishini kutmaslik uchun)."""
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

from common import FONTS

FDIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


@lru_cache(maxsize=None)
def _font(name, size):
    return ImageFont.truetype(str(FDIR / FONTS[name][0]), size)


def tw(name, size, text):
    return int(round(_font(name, size).getlength(text)))
