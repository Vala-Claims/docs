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
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGES_DIR = ROOT / "images"
CATALOG_PATH = IMAGES_DIR / "README.md"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


@dataclass(frozen=True)
class Asset:
    path: Path
    relative_path: str
    width: int | None
    height: int | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--validate", action="store_true", help="Validate screenshots, references, and the catalog")
    action.add_argument("--write-catalog", action="store_true", help="Write the current screenshot catalog to images/README.md")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    return parser.parse_args()


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24 and data[12:16] == b"IHDR":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    return None


def gif_dimensions(data: bytes) -> tuple[int, int] | None:
    if data[:6] in {b"GIF87a", b"GIF89a"} and len(data) >= 10:
        return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little")
    return None


def jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    position = 2
    while position + 9 < len(data):
        if data[position] != 0xFF:
            return None
        while position < len(data) and data[position] == 0xFF:
            position += 1
        marker = data[position]
        position += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if position + 2 > len(data):
            return None
        length = int.from_bytes(data[position : position + 2], "big")
        if length < 2 or position + length > len(data):
            return None
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if length < 7:
                return None
            return (
                int.from_bytes(data[position + 5 : position + 7], "big"),
                int.from_bytes(data[position + 3 : position + 5], "big"),
            )
        position += length
    return None


def webp_dimensions(data: bytes) -> tuple[int, int] | None:
    if not (len(data) >= 16 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
        return None
    # WebP has several encodings. The signature is enough to catch corrupt
    # uploads; dimensions are intentionally omitted when they are not trivial
    # to derive without adding an image dependency.
    return (0, 0)


def image_dimensions(path: Path) -> tuple[int | None, int | None]:
    data = path.read_bytes()
    for decoder in (png_dimensions, gif_dimensions, jpeg_dimensions, webp_dimensions):
        dimensions = decoder(data)
        if dimensions is not None:
            return dimensions
    raise ValueError("file content is not a supported image")


def collect_assets(root: Path) -> tuple[list[Asset], list[str]]:
    images_dir = root / "images"
    assets: list[Asset] = []
    errors: list[str] = []
    if not images_dir.is_dir():
        return [], ["images directory is missing"]

    seen_stems: dict[tuple[str, str], Path] = {}
    for path in sorted(candidate for candidate in images_dir.rglob("*") if candidate.is_file() and candidate.name != "README.md"):
        suffix = path.suffix.lower()
        relative = path.relative_to(root).as_posix()
        if suffix not in SUPPORTED_EXTENSIONS:
            errors.append(f"{relative}: unsupported format ({suffix or 'no extension'})")
            continue
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.stem):
            errors.append(f"{relative}: use lowercase kebab-case filenames")
        try:
            width, height = image_dimensions(path)
        except ValueError as exc:
            errors.append(f"{relative}: {exc}")
            continue
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
    target = root / reference.lstrip("/")
    if not target.is_file():
        errors.append(f"{page}: {reference} does not resolve to an image in this repository")


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
