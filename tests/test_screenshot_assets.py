from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "screenshot_assets.py"
SPEC = importlib.util.spec_from_file_location("screenshot_assets", SCRIPT)
assert SPEC and SPEC.loader
assets = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = assets
SPEC.loader.exec_module(assets)


PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x03\x08\x02\x00\x00\x00"
JPEG = b"\xff\xd8\xff\xc0\x00\x07\x08\x00\x03\x00\x02\x00\xff\xd9"
GIF = b"GIF89a\x02\x00\x03\x00"
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 "


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

    def test_accepts_supported_image_formats(self) -> None:
        for extension, image in (("jpg", JPEG), ("gif", GIF), ("webp", WEBP)):
            with self.subTest(extension=extension):
                root = self.make_root()
                self.write_asset(root, f"example.{extension}", image)

                _, errors = assets.collect_assets(root)

                self.assertEqual([], errors)

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

    def test_requires_a_current_catalog(self) -> None:
        root = self.make_root()
        self.write_asset(root)

        errors = assets.validate(root)

        self.assertIn("images/README.md is missing; run with --write-catalog", errors)


if __name__ == "__main__":
    unittest.main()
