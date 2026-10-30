# Vala Help Center

Customer-facing documentation for [Vala](https://valaclaims.com), the AI operating system for VA disability claims.

## Repository identity

This repository is the source for Vala's customer-facing Help Center. Its GitHub name is [`Vala-Claims/docs`](https://github.com/Vala-Claims/docs), despite the generic `docs` repository name.

It is not the Vala application repository or a general internal-documentation store. Mintlify configuration, the app's documentation-impact workflow, and the opt-in `/docs-showcase` asset workflow reference this repository identity and its `images/` destination. Do not rename the repository or change those integration paths without a verified downstream migration plan.

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

## Source ownership and portability

`Vala-Claims/docs` is the canonical source for customer-facing Help Center content. Keep MDX pages, images, navigation, configuration, redirects, source provenance, automation inputs, and approval evidence in version control. Mintlify renders and publishes this source; it must not be the sole location for critical institutional knowledge, source evidence, automation state, or approval logic.

Mintlify-specific dependencies include the `docs.json` schema and its theme, navigation, contextual options, and Mintlify MDX components. A future migration would retain this repository, map `docs.json` to the target platform's configuration, and replace Mintlify-specific components with the target's equivalents. This repository has not completed or tested such a migration.

The production Mintlify workspace connection, deployment history, and current custom domain require authenticated workspace readback to verify. Do not treat a local Mintlify validation as proof that a source change has published.

## Screenshot assets

Documentation screenshots live in [`images/README.md`](images/README.md). It is the repository gallery: it lists every stable Mintlify path and the command contributors use to refresh it after adding a generated image.

Run the deterministic preflight before opening a documentation PR:

```bash
python3 scripts/screenshot_assets.py --write-catalog
python3 scripts/screenshot_assets.py --validate
```

The preflight accepts PNG, JPEG, GIF, and WebP screenshots, checks file content and naming collisions, confirms every local `/images/...` MDX reference resolves, and requires meaningful alt text.

## Publishing

Submit documentation changes through a pull request. Do not merge unvalidated navigation or link changes.
