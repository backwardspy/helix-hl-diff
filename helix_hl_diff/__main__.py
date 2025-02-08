import logging
import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from urllib.request import urlopen

from helix_hl_diff import helix
from helix_hl_diff.img_compare import diff_images
from helix_hl_diff.render import render

HELIX_VERSION = os.getenv("HELIX_VERSION", "25.01.1")
HELIX_TARGET = os.getenv("HELIX_TARGET", "x86_64-windows")

BASE_BRANCH = os.getenv("BASE_BRANCH", "main")
CMP_BRANCH = os.getenv("CMP_BRANCH", "renovate/catppuccin-whiskers-2.x")

BASE_BRANCH_PATHSAFE = "-".join(Path(BASE_BRANCH).parts)
CMP_BRANCH_PATHSAFE = "-".join(Path(CMP_BRANCH).parts)

FLAVOURS = ["latte", "frappe", "macchiato", "mocha"]

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

        for branch, branch_pathsafe in [
            (BASE_BRANCH, BASE_BRANCH_PATHSAFE),
            (CMP_BRANCH, CMP_BRANCH_PATHSAFE),
        ]:
            for flavour in FLAVOURS:
                paths = Paths(
                    hx,
                    runtime,
                    ansi=Path("output") / branch_pathsafe / "ansi" / flavour,
                    images=Path("output") / branch_pathsafe / "images" / flavour,
                )

                url = f"https://raw.githubusercontent.com/catppuccin/helix/refs/heads/{branch}/themes/default/catppuccin_{flavour}.toml"
                theme_file = paths.runtime / "themes/catppuccin.toml"
                theme_file.parent.mkdir(parents=True, exist_ok=True)
                logger.info("downloading theme from %s into %s", url, theme_file)
                with urlopen(url) as resp:
                    theme_file.write_bytes(resp.read())

                render_samples(paths)

        for flavour in FLAVOURS:
            base_imgs = Path("output") / BASE_BRANCH_PATHSAFE / "images" / flavour
            for img in base_imgs.iterdir():
                cmp_img = (
                    Path("output") / CMP_BRANCH_PATHSAFE / "images" / flavour / img.name
                )
                _, diff_img = diff_images(img, cmp_img)
                if diff_img:
                    diffs_path = Path("output") / "diffs" / img.name
                    diffs_path.parent.mkdir(parents=True, exist_ok=True)
                    diff_img.save(diffs_path)


def render_samples(paths: Paths) -> None:
    # sorry
    subprocess.run("mode con:cols=80 lines=24", shell=True, check=True)
    for sample in Path("samples").iterdir():
        render_sample(sample, paths)


def render_sample(sample: Path, paths: Paths) -> None:
    logger.info("ansifying %s with %s", sample, paths.hx)
    out_path = paths.ansi / f"{sample.name}.ansi"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as out_file:
        args = [
            str(paths.hx.absolute()),
            "--config",
            str(Path("resources/helix-config.toml").absolute()),
            str(sample.absolute()),
        ]

        env = {
            "HELIX_RUNTIME": str(paths.runtime.absolute()),
        }
        logger.debug("args: %s // env: %s", " ".join(args), str(env))

        p = subprocess.Popen(
            args,
            env=env,
            stdout=out_file,
        )
        sleep(0.2)
        p.send_signal(signal.SIGTERM)
        p.wait(3)
        p.kill()
        p.wait()
        sleep(0.2)

    image_path = paths.images / f"{sample.stem}.png"
    logger.info("rendering %s into %s", out_path, image_path)
    render(out_path, image_path)


if __name__ == "__main__":
    main()
