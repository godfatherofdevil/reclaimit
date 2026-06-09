import os
from datetime import UTC, datetime

from reclaimit.core import MediaKind, scan_local_media


def test_scan_local_media_includes_nested_regular_files(tmp_path):
    nested = tmp_path / "nested" / "album"
    nested.mkdir(parents=True)
    image = nested / "IMG_0001.JPG"
    image.write_bytes(b"image")

    catalog = scan_local_media(tmp_path)

    assert [item.identity for item in catalog.items] == ["/nested/album/IMG_0001.JPG"]


def test_scan_local_media_skips_hidden_files_and_directories(tmp_path):
    visible = tmp_path / "visible.png"
    visible.write_bytes(b"visible")
    hidden_file = tmp_path / ".hidden.jpg"
    hidden_file.write_bytes(b"hidden")
    hidden_dir = tmp_path / ".private"
    hidden_dir.mkdir()
    (hidden_dir / "secret.mov").write_bytes(b"secret")
    nested_hidden = tmp_path / "album"
    nested_hidden.mkdir()
    (nested_hidden / ".sidecar.mp4").write_bytes(b"sidecar")

    catalog = scan_local_media(tmp_path)

    assert [item.identity for item in catalog.items] == ["/visible.png"]


def test_scan_local_media_detects_media_kind_by_extension(tmp_path):
    photo = tmp_path / "photo.heic"
    video = tmp_path / "clip.MP4"
    other = tmp_path / "notes.txt"
    photo.write_bytes(b"photo")
    video.write_bytes(b"video")
    other.write_bytes(b"other")

    catalog = scan_local_media(tmp_path)
    kinds = {item.identity: item.kind for item in catalog.items}

    assert kinds == {
        "/clip.MP4": MediaKind.VIDEO,
        "/notes.txt": MediaKind.OTHER,
        "/photo.heic": MediaKind.PHOTO,
    }


def test_scan_local_media_populates_size_and_modified_time(tmp_path):
    media = tmp_path / "IMG_0002.jpeg"
    media.write_bytes(b"content")
    modified_at = 1_767_225_600

    os.utime(media, (modified_at, modified_at))

    catalog = scan_local_media(tmp_path)
    item = catalog.items[0]

    assert item.size == len(b"content")
    assert item.modified_at == datetime.fromtimestamp(modified_at, tz=UTC)
