#!/usr/bin/env python3
"""Validate and catalog Mintlify documentation screenshots.

Usage:
  python3 scripts/screenshot_assets.py --validate
  python3 scripts/screenshot_assets.py --write-catalog

The Help Center publishes repository files below /images directly. This script
keeps that workflow deterministic without introducing a separate upload or
media-management service.
"""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
FORMAT_BY_EXTENSION = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".gif": "GIF", ".webp": "WebP"}


@dataclass(frozen=True)
class Asset:
    path: Path
    relative_path: str
    width: int | None
    height: int | None


@dataclass(frozen=True)
class ImageInfo:
    format: str
    width: int | None
    height: int | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--validate", action="store_true", help="Validate screenshots, references, and the catalog")
    action.add_argument("--write-catalog", action="store_true", help="Write the current screenshot catalog to images/README.md")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    return parser.parse_args()


def png_info(data: bytes) -> ImageInfo | None:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    position = 8
    width = height = None
    idat_chunks: list[bytes] = []
    seen_iend = False
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError("incomplete PNG chunk")
        length = int.from_bytes(data[position : position + 4], "big")
        chunk_type = data[position + 4 : position + 8]
        end = position + 12 + length
        if end > len(data):
            raise ValueError("incomplete PNG chunk")
        payload = data[position + 8 : position + 8 + length]
        crc = int.from_bytes(data[position + 8 + length : end], "big")
        if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != crc:
            raise ValueError("PNG chunk checksum does not match")
        if width is None:
            if chunk_type != b"IHDR" or length != 13:
                raise ValueError("PNG must begin with one IHDR chunk")
            width = int.from_bytes(payload[0:4], "big")
            height = int.from_bytes(payload[4:8], "big")
            if not width or not height:
                raise ValueError("PNG dimensions must be non-zero")
        elif chunk_type == b"IHDR":
            raise ValueError("PNG has more than one IHDR chunk")
        if chunk_type == b"IDAT":
            idat_chunks.append(payload)
        if chunk_type == b"IEND":
            if length != 0 or not idat_chunks:
                raise ValueError("PNG is missing image data or has an invalid IEND chunk")
            if end != len(data):
                raise ValueError("PNG has data after IEND")
            seen_iend = True
            break
        position = end
    if not seen_iend:
        raise ValueError("PNG is missing IEND")
    try:
        decoded_image_data = zlib.decompress(b"".join(idat_chunks))
    except zlib.error as exc:
        raise ValueError("PNG image data is incomplete") from exc
    if not decoded_image_data:
        raise ValueError("PNG is missing decoded image data")
    return ImageInfo("PNG", width, height)


def consume_gif_sub_blocks(data: bytes, position: int) -> int:
    while True:
        if position >= len(data):
            raise ValueError("incomplete GIF data block")
        length = data[position]
        position += 1
        if length == 0:
            return position
        if position + length > len(data):
            raise ValueError("incomplete GIF data block")
        position += length


def gif_info(data: bytes) -> ImageInfo | None:
    if data[:6] not in {b"GIF87a", b"GIF89a"}:
        return None
    if len(data) < 13:
        raise ValueError("incomplete GIF header")
    width = int.from_bytes(data[6:8], "little")
    height = int.from_bytes(data[8:10], "little")
    if not width or not height:
        raise ValueError("GIF dimensions must be non-zero")
    position = 13
    if data[10] & 0x80:
        color_table_length = 3 * (2 ** ((data[10] & 0x07) + 1))
        if position + color_table_length > len(data):
            raise ValueError("incomplete GIF color table")
        position += color_table_length
    saw_image = False
    while position < len(data):
        introducer = data[position]
        position += 1
        if introducer == 0x3B:
            if not saw_image or position != len(data):
                raise ValueError("GIF is missing image data or has trailing data")
            return ImageInfo("GIF", width, height)
        if introducer == 0x21:
            if position >= len(data):
                raise ValueError("incomplete GIF extension")
            label = data[position]
            position += 1
            if label == 0xF9:
                if position + 6 > len(data) or data[position] != 4 or data[position + 5] != 0:
                    raise ValueError("invalid GIF graphic control extension")
                position += 6
            elif label in {0x01, 0xFF}:
                if position >= len(data):
                    raise ValueError("incomplete GIF extension")
                block_length = data[position]
                position += 1
                if position + block_length > len(data):
                    raise ValueError("incomplete GIF extension")
                position = consume_gif_sub_blocks(data, position + block_length)
            else:
                position = consume_gif_sub_blocks(data, position)
            continue
        if introducer != 0x2C or position + 9 > len(data):
            raise ValueError("invalid GIF block")
        descriptor = data[position : position + 9]
        position += 9
        if descriptor[8] & 0x80:
            color_table_length = 3 * (2 ** ((descriptor[8] & 0x07) + 1))
            if position + color_table_length > len(data):
                raise ValueError("incomplete GIF color table")
            position += color_table_length
        if position >= len(data) or not 2 <= data[position] <= 8:
            raise ValueError("invalid GIF image data")
        saw_image = True
        position = consume_gif_sub_blocks(data, position + 1)
    raise ValueError("GIF is missing trailer")


JPEG_SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def jpeg_info(data: bytes) -> ImageInfo | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    position = 2
    width = height = None
    while position < len(data):
        if data[position] != 0xFF:
            raise ValueError("invalid JPEG marker")
        while position < len(data) and data[position] == 0xFF:
            position += 1
        if position >= len(data):
            raise ValueError("incomplete JPEG marker")
        marker = data[position]
        position += 1
        if marker == 0xD9:
            if width is None or height is None or position != len(data):
                raise ValueError("JPEG is missing image data or has trailing data")
            return ImageInfo("JPEG", width, height)
        if marker in {0xD8, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if position + 2 > len(data):
            raise ValueError("incomplete JPEG segment")
        length = int.from_bytes(data[position : position + 2], "big")
        end = position + length
        if length < 2 or end > len(data):
            raise ValueError("incomplete JPEG segment")
        payload = data[position + 2 : end]
        if marker in JPEG_SOF_MARKERS:
            if len(payload) < 6:
                raise ValueError("invalid JPEG frame header")
            height = int.from_bytes(payload[1:3], "big")
            width = int.from_bytes(payload[3:5], "big")
            components = payload[5]
            if not width or not height or len(payload) != 6 + components * 3:
                raise ValueError("invalid JPEG frame header")
        if marker == 0xDA:
            if width is None or height is None or end >= len(data) - 2 or not data.endswith(b"\xff\xd9"):
                raise ValueError("JPEG is missing image data or EOI")
            return ImageInfo("JPEG", width, height)
        position = end
    raise ValueError("JPEG is missing EOI")


def webp_info(data: bytes) -> ImageInfo | None:
    if not data.startswith(b"RIFF"):
        return None
    if len(data) < 12 or data[8:12] != b"WEBP":
        raise ValueError("invalid WebP RIFF header")
    if int.from_bytes(data[4:8], "little") != len(data) - 8:
        raise ValueError("incomplete WebP RIFF container")
    position = 12
    image_dimensions: tuple[int, int] | None = None
    while position < len(data):
        if position + 8 > len(data):
            raise ValueError("incomplete WebP chunk")
        chunk_type = data[position : position + 4]
        length = int.from_bytes(data[position + 4 : position + 8], "little")
        end = position + 8 + length
        if end > len(data):
            raise ValueError("incomplete WebP chunk")
        payload = data[position + 8 : end]
        if chunk_type == b"VP8 ":
            if len(payload) < 10 or payload[3:6] != b"\x9d\x01\x2a":
                raise ValueError("invalid WebP VP8 image data")
            image_dimensions = (int.from_bytes(payload[6:8], "little") & 0x3FFF, int.from_bytes(payload[8:10], "little") & 0x3FFF)
        elif chunk_type == b"VP8L":
            if len(payload) < 5 or payload[0] != 0x2F:
                raise ValueError("invalid WebP VP8L image data")
            bits = int.from_bytes(payload[1:5], "little")
            image_dimensions = ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
        elif chunk_type == b"VP8X":
            if len(payload) != 10:
                raise ValueError("invalid WebP VP8X image data")
            image_dimensions = (
                int.from_bytes(payload[4:7], "little") + 1,
                int.from_bytes(payload[7:10], "little") + 1,
            )
        position = end + (length % 2)
    if position != len(data) or image_dimensions is None or not all(image_dimensions):
        raise ValueError("WebP is missing image data")
    return ImageInfo("WebP", *image_dimensions)


def image_info(path: Path) -> ImageInfo:
    data = path.read_bytes()
    for decoder in (png_info, gif_info, jpeg_info, webp_info):
        info = decoder(data)
        if info is not None:
            return info
    raise ValueError("file content is not a supported image")


def collect_assets(root: Path) -> tuple[list[Asset], list[str]]:
    images_dir = root / "images"
    assets: list[Asset] = []
    errors: list[str] = []
    if not images_dir.is_dir():
        return [], ["images directory is missing"]

    images_root = images_dir.resolve()
    seen_stems: dict[tuple[str, str], Path] = {}
    for path in sorted(candidate for candidate in images_dir.rglob("*") if candidate.is_file() and candidate.name != "README.md"):
        suffix = path.suffix.lower()
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or not is_within(path.resolve(), images_root):
            errors.append(f"{relative}: screenshots must be regular files inside images/")
            continue
        if suffix not in SUPPORTED_EXTENSIONS:
            errors.append(f"{relative}: unsupported format ({suffix or 'no extension'})")
            continue
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.stem):
            errors.append(f"{relative}: use lowercase kebab-case filenames")
        try:
            info = image_info(path)
        except ValueError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        expected_format = FORMAT_BY_EXTENSION[suffix]
        if info.format != expected_format:
            errors.append(f"{relative}: {expected_format} extension conflicts with detected {info.format} content")
            continue
        width, height = info.width, info.height
        if width == 0 or height == 0:
            width = height = None
        key = (path.parent.relative_to(images_dir).as_posix(), path.stem)
        if key in seen_stems:
            errors.append(f"{relative}: collides with {seen_stems[key].relative_to(root).as_posix()} (same path stem)")
        else:
            seen_stems[key] = path
        assets.append(Asset(path=path, relative_path=relative, width=width, height=height))
    return assets, errors


MARKDOWN_IMAGE = re.compile(r"!\[([^\]]*)\]\((/images/[^\s)]+)(?:\s+[^)]*)?\)")
HTML_IMAGE = re.compile(r"<img\b(?P<attributes>[^>]*)>", re.IGNORECASE)
ATTRIBUTE = re.compile(r"\b(?P<name>src|alt)\s*=\s*(['\"])(?P<value>.*?)\2", re.IGNORECASE)


def referenced_images(root: Path) -> list[str]:
    errors: list[str] = []
    for page in sorted(root.rglob("*.mdx")):
        text = page.read_text(encoding="utf-8")
        display_path = page.relative_to(root).as_posix()
        for alt, reference in MARKDOWN_IMAGE.findall(text):
            verify_reference(root, display_path, reference, alt, errors)
        for tag in HTML_IMAGE.finditer(text):
            attributes = {match.group("name").lower(): match.group("value") for match in ATTRIBUTE.finditer(tag.group("attributes"))}
            reference = attributes.get("src")
            if reference and reference.startswith("/images/"):
                verify_reference(root, display_path, reference, attributes.get("alt", ""), errors)
    return errors


def verify_reference(root: Path, page: str, reference: str, alt: str, errors: list[str]) -> None:
    if not alt.strip():
        errors.append(f"{page}: {reference} must have meaningful alt text")
    try:
        target = resolve_image_reference(root, reference)
    except ValueError as exc:
        errors.append(f"{page}: {reference} {exc}")
        return
    if not target.is_file():
        errors.append(f"{page}: {reference} does not resolve to an image in this repository")


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def decode_reference(reference: str) -> str:
    decoded = reference
    while True:
        next_value = unquote(decoded)
        if next_value == decoded:
            return decoded
        decoded = next_value


def resolve_image_reference(root: Path, reference: str) -> Path:
    decoded = decode_reference(reference)
    parsed = urlsplit(decoded)
    path = parsed.path.replace("\\", "/")
    if not path.startswith("/images/"):
        raise ValueError("must use a root-relative /images/ path")
    if ".." in path.split("/"):
        raise ValueError("must not contain traversal segments")
    normalized = posixpath.normpath(path)
    if not normalized.startswith("/images/"):
        raise ValueError("must remain inside images/")
    images_root = (root / "images").resolve()
    target = (root / normalized.lstrip("/")).resolve()
    if not is_within(target, images_root):
        raise ValueError("must resolve inside images/")
    if target.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("must reference a supported image format")
    return target


def render_catalog(assets: list[Asset]) -> str:
    lines = [
        "# Screenshot catalog",
        "",
        "This is the repository gallery for Help Center screenshots. Mintlify publishes files in `images/` at the same root-relative path, so use the reference shown below in an MDX page.",
        "",
        "## Add or update a screenshot",
        "",
        "1. Capture only a controlled demo organization with synthetic data. Do not add PHI, PII, claim numbers, customer names, or email addresses.",
        "2. Save the file under `images/<product-area>/`. For new screenshots, use lowercase kebab-case names in the form `<workflow>-<step>-<variant>.png`. Existing paths are stable and must not be renamed only to fit this convention.",
        "3. Use PNG, JPEG, GIF, or WebP. Before committing, run `python3 scripts/screenshot_assets.py --write-catalog`, `python3 scripts/screenshot_assets.py --validate`, `mint validate`, and `mint broken-links`.",
        "4. Reference an image with meaningful alt text, for example: `![Client list showing the Add Client button](/images/veteran-intake/clients-list.png)`.",
        "",
        "## Available screenshots",
        "",
        "| Asset | Mintlify reference | Dimensions |",
        "| --- | --- | --- |",
    ]
    for asset in assets:
        dimensions = f"{asset.width} × {asset.height}" if asset.width and asset.height else "Available in source file"
        reference = "/" + asset.relative_path
        lines.append(f"| `{asset.relative_path}` | `{reference}` | {dimensions} |")
    lines.extend(["", "The catalog is generated by `scripts/screenshot_assets.py`; do not edit the table by hand.", ""])
    return "\n".join(lines)


def validate(root: Path, require_catalog: bool = True) -> list[str]:
    assets, errors = collect_assets(root)
    errors.extend(referenced_images(root))
    if require_catalog:
        catalog_path = root / "images" / "README.md"
        expected = render_catalog(assets)
        if not catalog_path.is_file():
            errors.append("images/README.md is missing; run with --write-catalog")
        elif catalog_path.read_text(encoding="utf-8") != expected:
            errors.append("images/README.md is out of date; run with --write-catalog")
    return errors


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    assets, errors = collect_assets(root)
    if args.write_catalog:
        if errors:
            print("Screenshot asset validation failed:", file=sys.stderr)
            print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
            return 1
        (root / "images" / "README.md").write_text(render_catalog(assets), encoding="utf-8")
        print("Updated images/README.md")
        return 0

    errors.extend(referenced_images(root))
    catalog_path = root / "images" / "README.md"
    if not catalog_path.is_file() or catalog_path.read_text(encoding="utf-8") != render_catalog(assets):
        errors.append("images/README.md is out of date; run with --write-catalog")
    if errors:
        print("Screenshot asset validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Validated {len(assets)} screenshot assets and documentation references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
