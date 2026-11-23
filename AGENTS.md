# Vala Help Center instructions

## About this project

- This is Vala's customer-facing Help Center, built with Mintlify.
- Pages are MDX files with YAML frontmatter.
- Configuration and navigation live in `docs.json`.
- Run `mint validate` and `mint broken-links` before publishing.
- Preserve `architecture/`, `internal/`, and `scripts/` unless a task explicitly changes the documentation automation system.

## Terminology

- Use “veteran” naturally for the person being represented.
- Use “Client” when referring to a visible Vala interface object, view, button, breadcrumb, or Client record. Do not rename the shipped interface label in prose.
- Use “organization” for a customer's shared Vala environment.
- Use “Ask Vala” and “vSign” with this exact capitalization.
- Use the current interface labels: **Templates** (not Library), **Templates > Questionnaires** (not Web Forms), **Workflows** (not Automations), **History** or **Workflow History** (not Execution Log), **Templates > Messages** (not Message Templates), and **Calls** (not Calls & Transcripts when naming the workspace).
- Describe Vala as supporting claim preparation. Do not describe it as legal advice or a replacement for professional review.

## Customer-education boundary

- Explain what customers can accomplish, where functionality lives, when to use it, verified permissions or availability, review responsibilities, and troubleshooting.
- Describe AI-assisted features by customer outcome. Do not expose prompts, model routing, orchestration, extraction pipelines, proprietary heuristics, confidence mechanics, internal processing architecture, or other engineering details that do not help a customer use Vala.

## Style

- Use active voice and second person.
- Keep sentences concise and paragraphs short.
- Use sentence case for headings.
- Bold confirmed interface labels.
- Use placeholders when product behavior has not been verified.
- Do not invent product behavior, availability, permissions, limits, or UI labels.

## Required page template

1. Overview
2. When to use
3. Prerequisites
4. Step-by-step
5. Best practices
6. Common mistakes
7. Related pages
