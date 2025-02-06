import tarfile
import zipfile
from enum import Enum
from io import BytesIO
from pathlib import Path


class ArchiveType(Enum):
    ZIP = "zip"
    TARBALL = "tarball"

    def ext(self) -> str:
        match self:
            case ArchiveType.ZIP:
                return ".zip"
            case ArchiveType.TARBALL:
                return ".tar.gz"


def extract(fd: BytesIO, *, path: Path, archive_type: ArchiveType) -> None:
    match archive_type:
        case ArchiveType.ZIP:
            _extract_zip(fd, path)
        case ArchiveType.TARBALL:
            _extract_tarball(fd, path)


def _extract_zip(fd: BytesIO, path: Path) -> None:
    zf = zipfile.ZipFile(fd)
    zf.extractall(path)  # noqa: S202


def _extract_tarball(fd: BytesIO, path: Path) -> None:
    tf = tarfile.TarFile(fileobj=fd)
    tf.extractall(path, filter="data")
