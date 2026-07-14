#!/usr/bin/env python3
"""Generate a documentation impact report from changed product files.

Usage:
  python scripts/docs_impact.py path/to/file ...
  git diff --name-only origin/main...HEAD | python scripts/docs_impact.py --stdin

Requires PyYAML:
  python -m pip install pyyaml
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
from collections import deque
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required. Run: python -m pip install pyyaml") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "architecture" / "docs-dependency-manifest.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="Changed product repository paths")
    parser.add_argument("--stdin", action="store_true", help="Read newline-delimited paths from stdin")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "pages" not in data:
        raise SystemExit(f"Invalid manifest: {path}")
    return data


def normalize(paths: list[str]) -> list[str]:
    return sorted({p.strip().lstrip("./") for p in paths if p.strip()})


def path_matches(path: str, pattern: str) -> bool:
    # fnmatch does not give ** special semantics, but its wildcard behavior is
    # sufficient for repository paths and keeps the implementation portable.
    return fnmatch.fnmatchcase(path, pattern)


def direct_page_matches(files: list[str], pages: dict[str, Any]) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = {}
    for page_id, page in pages.items():
        patterns = page.get("upstream_paths", []) or []
        hit_files = [path for path in files if any(path_matches(path, pat) for pat in patterns)]
        if hit_files:
            matches[page_id] = hit_files
    return matches


def infer_features(files: list[str], feature_edges: dict[str, Any]) -> set[str]:
    inferred: set[str] = set()
    lowered = [(path, path.lower()) for path in files]
    aliases = {
        "primary_point_of_contact": ("primarypoc", "primary_poc", "primary-contact", "primary_contact"),
        "signing_packets": ("vsign", "esign", "envelope", "signing"),
        "pdf_autofill": ("pdf", "autofill", "form"),
        "rating_decisions": ("rating_decision", "ratingdecision"),
        "feature_visibility": ("entitlement", "feature_flag", "visibility"),
        "quicksubmit": ("quicksubmit", "quick_submit", "browser-extension", "extension/"),
    }
    for feature in feature_edges:
        tokens = set(feature.lower().split("_"))
        tokens.update(aliases.get(feature, ()))
        for _, path_lower in lowered:
            if any(token and token in path_lower for token in tokens):
                inferred.add(feature)
                break
    return inferred


def expand_impacts(
    direct: dict[str, list[str]],
    inferred_features: set[str],
    pages: dict[str, Any],
    feature_edges: dict[str, Any],
) -> tuple[set[str], dict[str, set[str]]]:
    impacted = set(direct)
    reasons: dict[str, set[str]] = {page: {"direct path match"} for page in direct}

    for feature in inferred_features:
        for page in feature_edges.get(feature, {}).get("affects", []) or []:
            impacted.add(page)
            reasons.setdefault(page, set()).add(f"feature: {feature}")

    queue = deque(impacted)
    while queue:
        page_id = queue.popleft()
        page = pages.get(page_id, {})
        for downstream in page.get("downstream_pages", []) or []:
            if downstream not in impacted:
                impacted.add(downstream)
                queue.append(downstream)
            reasons.setdefault(downstream, set()).add(f"downstream of {page_id}")

    return impacted, reasons


def build_report(files: list[str], manifest: dict[str, Any]) -> dict[str, Any]:
    pages = manifest.get("pages", {})
    feature_edges = manifest.get("feature_edges", {})
    direct = direct_page_matches(files, pages)
    features = infer_features(files, feature_edges)
    impacted, reasons = expand_impacts(direct, features, pages, feature_edges)

    page_reports = []
    for page_id in sorted(impacted):
        page = pages.get(page_id, {})
        page_reports.append(
            {
                "id": page_id,
                "path": page.get("path"),
                "review": page.get("review", []),
                "reasons": sorted(reasons.get(page_id, set())),
                "matching_files": direct.get(page_id, []),
            }
        )

    return {
        "changed_files": files,
        "inferred_features": sorted(features),
        "impacted_pages": page_reports,
        "docs_update_likely": bool(page_reports),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["## Documentation impact", ""]
    if not report["impacted_pages"]:
        lines.extend(
            [
                "No customer-facing documentation impact was detected.",
                "",
                "A human should still review backend changes that alter behavior, limits, permissions, or generated output.",
            ]
        )
        return "\n".join(lines)

    if report["inferred_features"]:
        lines.append("**Detected features:** " + ", ".join(f"`{x}`" for x in report["inferred_features"]))
        lines.append("")

    lines.append("| Page | Required review | Why |")
    lines.append("|---|---|---|")
    for page in report["impacted_pages"]:
        review = ", ".join(page["review"]) or "human review"
        why = "; ".join(page["reasons"])
        path = page["path"] or page["id"]
        lines.append(f"| `{path}` | {review} | {why} |")

    lines.extend(["", "### Changed files", ""])
    lines.extend(f"- `{path}`" for path in report["changed_files"])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    files = list(args.files)
    if args.stdin:
        files.extend(sys.stdin.read().splitlines())
    files = normalize(files)
    if not files:
        raise SystemExit("No changed files supplied")

    manifest = load_manifest(args.manifest)
    report = build_report(files, manifest)

    if args.format == "json":
        import json

        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
