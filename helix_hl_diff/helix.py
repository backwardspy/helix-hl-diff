import logging
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from helix_hl_diff.archive import ArchiveType, extract

logger = logging.getLogger("hhd")


def _archive_type(target: str) -> ArchiveType:
    if "windows" in target:
        return ArchiveType.ZIP
    else:
        return ArchiveType.TARBALL


def release_artifact_name(version: str, target: str) -> str:
    ext = _archive_type(target).ext()
    return f"helix-{version}-{target}{ext}"


def download_helix(
    path: Path,
    *,
    version: str,
    target: str,
):
    artifact = release_artifact_name(version, target)
    url = (
        f"https://github.com/helix-editor/helix/releases/download/{version}/{artifact}"
    )
    with urlopen(url) as resp:
        logger.debug("downloading helix release artifact from %s", url)
        buf = BytesIO(resp.read())
        logger.debug("extracting archive into %s", path)
        extract(buf, path=path, archive_type=_archive_type(target))
        logger.debug("helix archive extracted into %s", path)
