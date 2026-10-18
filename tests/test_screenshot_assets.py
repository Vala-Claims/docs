from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "screenshot_assets.py"
SPEC = importlib.util.spec_from_file_location("screenshot_assets", SCRIPT)
assert SPEC and SPEC.loader
assets = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = assets
SPEC.loader.exec_module(assets)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return len(payload).to_bytes(4, "big") + kind + payload + (zlib.crc32(kind + payload) & 0xFFFFFFFF).to_bytes(4, "big")


def valid_png(width: int = 2, height: int = 3) -> bytes:
    header = width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00"
    scanlines = b"".join(b"\x00" + (b"\x00\x00\x00" * width) for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) + png_chunk(b"IDAT", zlib.compress(scanlines)) + png_chunk(b"IEND", b"")


def valid_jpeg() -> bytes:
    frame = b"\x08\x00\x03\x00\x02\x01\x01\x11\x00"
    scan = b"\x01\x01\x00\x00\x3f\x00"
    return b"\xff\xd8\xff\xc0" + (len(frame) + 2).to_bytes(2, "big") + frame + b"\xff\xda" + (len(scan) + 2).to_bytes(2, "big") + scan + b"\x00\xff\xd9"


def valid_webp() -> bytes:
    payload = b"\x00\x00\x00\x9d\x01\x2a\x02\x00\x03\x00"
    body = b"WEBP" + b"VP8 " + len(payload).to_bytes(4, "little") + payload
    return b"RIFF" + len(body).to_bytes(4, "little") + body


PNG = valid_png()
JPEG = valid_jpeg()
GIF = b"GIF89a\x02\x00\x03\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x02\x00\x03\x00\x00\x02\x02D\x01\x00;"
WEBP = valid_webp()


class ScreenshotAssetsTests(unittest.TestCase):
    def make_root(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "images" / "reports").mkdir(parents=True)
        (root / "pages").mkdir()
        return root

    def write_asset(self, root: Path, name: str = "list.png", data: bytes = PNG) -> Path:
        path = root / "images" / "reports" / name
        path.write_bytes(data)
        return path

    def write_catalog(self, root: Path) -> None:
        screenshot_assets, errors = assets.collect_assets(root)
        self.assertEqual([], errors)
        (root / "images" / "README.md").write_text(assets.render_catalog(screenshot_assets), encoding="utf-8")

    def test_accepts_valid_png_and_resolves_markdown_reference(self) -> None:
        root = self.make_root()
        self.write_asset(root)
        (root / "pages" / "reports.mdx").write_text(
            "![Reports list showing submitted reports](/images/reports/list.png)\n", encoding="utf-8"
        )
        self.write_catalog(root)

        self.assertEqual([], assets.validate(root))

    def test_rejects_invalid_image_content(self) -> None:
        root = self.make_root()
        self.write_asset(root, data=b"not an image")

        _, errors = assets.collect_assets(root)

        self.assertIn("images/reports/list.png: file content is not a supported image", errors)

    def test_rejects_truncated_png_even_with_a_valid_header(self) -> None:
        root = self.make_root()
        self.write_asset(root, data=PNG[:24])

        _, errors = assets.collect_assets(root)

        self.assertTrue(any("incomplete PNG" in error for error in errors))

    def test_accepts_supported_image_formats(self) -> None:
        for extension, image in (("jpg", JPEG), ("jpeg", JPEG), ("gif", GIF), ("webp", WEBP)):
            with self.subTest(extension=extension):
                root = self.make_root()
                self.write_asset(root, f"example.{extension}", image)

                _, errors = assets.collect_assets(root)

                self.assertEqual([], errors)

    def test_rejects_extension_content_mismatch(self) -> None:
        root = self.make_root()
        self.write_asset(root, "list.png", JPEG)

        _, errors = assets.collect_assets(root)

        self.assertIn("images/reports/list.png: PNG extension conflicts with detected JPEG content", errors)

    def test_rejects_same_stem_with_different_extensions(self) -> None:
        root = self.make_root()
        self.write_asset(root, "list.png")
        self.write_asset(root, "list.webp", WEBP)

        _, errors = assets.collect_assets(root)

        self.assertTrue(any("collides with images/reports/list.png" in error for error in errors))

    def test_reports_broken_references_and_missing_alt_text(self) -> None:
        root = self.make_root()
        self.write_asset(root)
        (root / "pages" / "reports.mdx").write_text("![](/images/reports/missing.png)\n", encoding="utf-8")
        self.write_catalog(root)

        errors = assets.validate(root)

        self.assertIn("pages/reports.mdx: /images/reports/missing.png must have meaningful alt text", errors)
        self.assertIn("pages/reports.mdx: /images/reports/missing.png does not resolve to an image in this repository", errors)

    def test_rejects_traversal_references_after_decoding(self) -> None:
        for reference in (
            "/images/../secret.png",
            "/images/%2e%2e/secret.png",
            "/images/%252e%252e/secret.png",
            "/images/reports%5c..%5c..%5csecret.png",
        ):
            with self.subTest(reference=reference):
                root = self.make_root()
                self.write_asset(root)
                (root / "secret.png").write_bytes(PNG)
                (root / "pages" / "reports.mdx").write_text(f"![Secret]({reference})\n", encoding="utf-8")
                self.write_catalog(root)

                errors = assets.validate(root)

                self.assertTrue(any("must not contain traversal segments" in error for error in errors))

    def test_accepts_normalized_in_directory_reference_with_a_query_and_fragment(self) -> None:
        root = self.make_root()
        self.write_asset(root)
        (root / "pages" / "reports.mdx").write_text(
            "![Reports list showing submitted reports](/images//reports/./list.png?version=1#preview)\n", encoding="utf-8"
        )
        self.write_catalog(root)

        self.assertEqual([], assets.validate(root))

    def test_requires_a_current_catalog(self) -> None:
        root = self.make_root()
        self.write_asset(root)

        errors = assets.validate(root)

        self.assertIn("images/README.md is missing; run with --write-catalog", errors)


if __name__ == "__main__":
    unittest.main()
