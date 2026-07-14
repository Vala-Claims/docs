# Vala Help Center

Customer-facing documentation for [Vala](https://valaclaims.com), the AI operating system for VA disability claims.

## Local development

The site is built with Mintlify. Install the current CLI, then run the preview from the repository root:

```bash
npm install -g mint
mint dev
```

The local preview is available at `http://localhost:3000`.

## Validation

Before opening a pull request, run:

```bash
mint validate
mint broken-links
```

Also confirm that every page in `docs.json` exists and every customer-facing page follows the standard structure:

- Overview
- When to use
- Prerequisites
- Step-by-step
- Best practices
- Common mistakes
- Related pages

## Documentation impact automation

The dependency manifest in `architecture/docs-dependency-manifest.yaml` maps product changes to customer-facing pages. The helper in `scripts/docs_impact.py` generates a review report for changed product files.

## Publishing

Submit documentation changes through a pull request. Do not merge unvalidated navigation or link changes.
