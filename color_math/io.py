from __future__ import annotations

import codecs
import os
import shutil
import tempfile
from pathlib import Path


def read_utf8(path: Path) -> tuple[str, bytes]:
    """Read UTF-8 text while retaining its exact original bytes."""
    source = path.read_bytes()
    body = (
        source[len(codecs.BOM_UTF8) :]
        if source.startswith(codecs.BOM_UTF8)
        else source
    )
    return body.decode("utf-8"), source


def encode_utf8(text: str, source: bytes) -> bytes:
    """Encode text with the source file's UTF-8 BOM convention."""
    bom = codecs.BOM_UTF8 if source.startswith(codecs.BOM_UTF8) else b""
    return bom + text.encode("utf-8")


def replace_bytes(path: Path, data: bytes, source: bytes) -> bool:
    """Atomically replace path, returning False when nothing changed."""
    if data == source:
        return False

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != source:
            raise OSError("file changed while it was being processed; refusing to overwrite")
        shutil.copymode(path, temporary)
        os.replace(temporary, path)
        return True
    finally:
        if descriptor != -1:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
