import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from stransi import Ansi, SetAttribute, SetColor
from stransi.attribute import Attribute
from stransi.color import ColorRole

ROWS = 20
COLS = 80
FONT_SIZE = 12
X_RATIO = 0.7
Y_RATIO = 1.3
CHR_WIDTH = int(FONT_SIZE * X_RATIO)
CHR_HEIGHT = int(FONT_SIZE * Y_RATIO)


def render(ansi_path: Path, output_image_path: Path):
    text = ansi_path.read_text()

    # remove unsupported control sequences
    pat = re.compile(r"(\x1b\[\?\d+h)|(\x1b\[\?\d+l)")

    text = pat.sub("", text)
    text = Ansi(text)

    fonts = {
        "regular": ImageFont.truetype(
            "resources/JetBrainsMono-Regular.ttf",
            size=FONT_SIZE,
        ),
        "italic": ImageFont.truetype(
            "resources/JetBrainsMono-Italic.ttf",
            size=FONT_SIZE,
        ),
    }
    img = Image.new(
        "RGB",
        (COLS * CHR_WIDTH, ROWS * CHR_HEIGHT),
        (255, 0, 255),
    )
    draw = ImageDraw.Draw(img)

    row, col = 0, 0
    fg = (255, 255, 255)
    bg = (0, 0, 0)
    style = "regular"

    for ins in text.instructions():
        if isinstance(ins, SetColor):
            if ins.role == ColorRole.FOREGROUND:
                if ins.color:
                    rgb = ins.color.rgb
                    fg = (int(rgb.red * 255), int(rgb.green * 255), int(rgb.blue * 255))
                else:
                    fg = (255, 255, 255)
            elif ins.role == ColorRole.BACKGROUND:
                if ins.color:
                    rgb = ins.color.rgb
                    bg = (int(rgb.red * 255), int(rgb.green * 255), int(rgb.blue * 255))
                else:
                    bg = (0, 0, 0)
        elif isinstance(ins, SetAttribute):
            match ins.attribute:
                case Attribute.ITALIC:
                    style = "italic"
                case Attribute.NOT_ITALIC:
                    style = "regular"
        elif isinstance(ins, str):
            for offset, chr in enumerate(ins):
                x = (col + offset) * CHR_WIDTH
                y = row * CHR_HEIGHT
                draw.rectangle(
                    (x, y, x + CHR_WIDTH, y + CHR_HEIGHT),
                    fill=bg,
                    width=0,
                )
                draw.text(
                    (x, y),
                    chr,
                    fill=fg,
                    font=fonts[style],
                )
            col += len(ins)
            if col >= COLS:
                col = 0
                row += 1

    img.save(output_image_path)


if __name__ == "__main__":
    input_path = Path(sys.argv[1])
    output_path = Path("rendered") / f"{input_path.stem}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render(input_path, output_path)
