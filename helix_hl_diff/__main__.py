import logging
import os
import signal
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

from helix_hl_diff import helix

HELIX_VERSION = os.getenv("HELIX_VERSION", "25.01.1")
HELIX_TARGET = os.getenv("HELIX_TARGET", "x86_64-windows")

logging.basicConfig(
    level=logging.getLevelNamesMapping()[os.getenv("LOG_LEVEL", "info").upper()],
)
logger = logging.getLogger("hhd")


def main() -> None:
    with TemporaryDirectory(
        prefix="helix-hl-diff",
        delete=os.getenv("HELIX_CLEANUP", "") != "false",
    ) as td_str:
        td = Path(td_str)

        helix.download_helix(td, version=HELIX_VERSION, target=HELIX_TARGET)
        hx = (
            td
            / f"helix-{HELIX_VERSION}-{HELIX_TARGET}"
            / ("hx.exe" if "windows" in HELIX_TARGET else "hx")
        )

        render_samples(hx)


def render_samples(hx: Path) -> None:
    for sample in Path("samples").iterdir():
        render_sample(hx, sample)


def render_sample(hx: Path, sample: Path) -> None:
    logger.info("rendering %s with %s", sample, hx)
    out_path = Path(f"ansi/{sample.name}.ansi")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as out_file:
        args = [
            str(hx.absolute()),
            "--config",
            str(Path("helix-config.toml").absolute()),
            str(sample.absolute()),
        ]
        logger.debug("args: %s", " ".join(args))
        p = subprocess.Popen(  # noqa: S603
            args,
            stdout=out_file,
            stderr=subprocess.PIPE,
        )
        sleep(0.5)
        p.send_signal(signal.SIGTERM)
        sleep(0.5)


if __name__ == "__main__":
    main()
