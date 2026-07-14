# Documentation Impact Automation

## Purpose

The first automation does not rewrite documentation. It identifies which customer-facing pages, screenshots, and walkthroughs require review when a product pull request changes Vala.

## Local usage

```bash
python -m pip install -r scripts/requirements.txt
git diff --name-only origin/main...HEAD | python scripts/docs_impact.py --stdin
```

The script reads `architecture/docs-dependency-manifest.yaml` and returns a Markdown table containing:

- affected documentation pages
- required text, screenshot, or walkthrough review
- the direct or downstream reason each page was flagged
- inferred product features

JSON output is available for CI automation:

```bash
git diff --name-only origin/main...HEAD \
  | python scripts/docs_impact.py --stdin --format json
```

## Intended product repository workflow

The `Vala-Claims/vala` repository should run the script on pull requests after checking out both repositories:

1. Check out the product PR.
2. Check out `Vala-Claims/docs` into a `vala-docs` directory.
3. Install `vala-docs/scripts/requirements.txt`.
4. Collect changed filenames from the product PR.
5. Run `vala-docs/scripts/docs_impact.py` using the docs manifest.
6. Post or update a `Documentation impact` section on the product PR.

## Initial behavior

The automation should be advisory during rollout.

- It must not block merges initially.
- It must not modify documentation automatically.
- A reviewer confirms whether the impact report is correct.
- False positives and false negatives should be used to improve the manifest.

After the impact analysis is trusted, the next phase can automatically open a draft docs PR containing proposed text and screenshot updates.

## Trigger categories now mapped

- Conditions and rating decisions
- Evidence and citations
- Timeline and chronology
- Tasks and assignments
- Automations and triggers
- Calls and transcripts
- QuickSubmit and browser extension
- Organization roles and permissions
- Billing, plans, editions, limits, and feature visibility
- Veterans, contacts, forms, PDF autofill, and vSign
- Chat with Vala and reports

## Required human exceptions

A backend-only change still requires review when it changes:

- visible behavior
- permissions
- plan availability or limits
- generated forms, reports, or signing packets
- customer-facing errors or terminology
