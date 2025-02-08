import logging
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

from ptyprocess import PtyProcessUnicode

from helix_hl_diff import helix
from helix_hl_diff.render import render

HELIX_VERSION = os.getenv("HELIX_VERSION", "25.01.1")
HELIX_TARGET = os.getenv("HELIX_TARGET", "x86_64-windows")

logging.basicConfig(
    format="[%(levelname)8s] %(message)s",
    level=logging.getLevelNamesMapping()[os.getenv("LOG_LEVEL", "info").upper()],
)
logger = logging.getLogger("hhd")


@dataclass(frozen=True)
class Paths:
    hx: Path
    runtime: Path
    ansi: Path
    images: Path


def main() -> None:
    with TemporaryDirectory(
        prefix="helix-hl-diff",
        delete=os.getenv("HELIX_CLEANUP", "") != "false",
    ) as td_str:
        td = Path(td_str)

        runtime = td / "runtime"
        runtime.mkdir()

        helix.download_helix(td, version=HELIX_VERSION, target=HELIX_TARGET)
        hx = (
            td
            / f"helix-{HELIX_VERSION}-{HELIX_TARGET}"
            / ("hx.exe" if "windows" in HELIX_TARGET else "hx")
        )

        for flavour in ["latte", "frappe", "macchiato", "mocha"]:
            paths = Paths(
                hx,
                runtime,
                ansi=Path("output/ansi") / flavour,
                images=Path("output/images") / flavour,
            )
            render_samples(paths)


def render_samples(paths: Paths) -> None:
    for sample in Path("samples").iterdir():
        render_sample(sample, paths)


def render_sample(sample: Path, paths: Paths) -> None:
    logger.info("ansifying %s with %s", sample, paths.hx)
    out_path = paths.ansi / f"{sample.name}.ansi"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as out_file:
        args = [
            str(paths.hx.absolute()),
            "--config",
            str(Path("resources/helix-config.toml").absolute()),
            str(sample.absolute()),
        ]
        env = {
            "HELIX_RUNTIME": str(paths.runtime.absolute()),
            "LINES": "24",
            "COLUMNS": "80",
            "TERM": "xterm-256color",
        }
        logger.debug("args: %s // env: %s", " ".join(args), str(env))
        p = PtyProcessUnicode.spawn(
            args,
            env=env,
            dimensions=(24, 80),
        )
        sleep(0.2)
        out_file.write(p.read(8192))
        p.close()
        sleep(0.2)

    image_path = paths.images / f"{sample.stem}.png"
    logger.info("rendering %s into %s", out_path, image_path)
    render(out_path, image_path)


if __name__ == "__main__":
    main()
