from pathlib import Path
from typing import Literal

from PIL import Image, ImageChops


def diff_images(
    base_path: Path,
    cmp_path: Path,
) -> tuple[Literal[True], Image.Image] | tuple[Literal[False], None]:
    """
    If images differ, returns true and the diff image, else returns false and none.
    """
    base = Image.open(base_path).convert("RGB")
    cmp = Image.open(cmp_path).convert("RGB")
    diff = ImageChops.difference(base, cmp)
    if diff.getbbox():
        return (True, diff)
    return (False, None)
