# Vala Documentation Architecture v1

This document defines how Vala's customer documentation is organized, maintained, and updated as the product changes.

## Objectives

The documentation system should:

- Help a new customer reach value without requiring live support for basic workflows.
- Reflect the current product, not an aspirational or outdated version of it.
- Identify documentation affected by UI, workflow, API, and dependency changes.
- Produce reviewable updates rather than publishing AI-generated changes automatically.
- Support written guides, screenshots, walkthrough videos, release notes, and future AI support experiences from one source of truth.

## Source-of-truth hierarchy

For current customer-visible behavior, use this order:

1. Production behavior in `app.valaclaims.com`
2. Implementation confirmed released to the relevant customer audience
3. Completed Linear acceptance criteria and context for that released behavior
4. Existing Help Center documentation

For governance, terminology, product claims, and authority, use this order:

1. Current canonical Vala Operating System
2. Current accepted Product decisions and applicable authoritative records
3. Historical or draft materials

Merged but unreleased code is not current customer functionality. If current behavior conflicts with canonical policy or accepted Product intent, surface the mismatch for review rather than silently resolving it.

## Audience

Primary audiences:

- VA-accredited attorneys
- VA-accredited claims agents
- Veteran Service Organizations
- Support staff working under accredited representatives
- Organization administrators

Secondary audiences:

- Implementation partners
- Integration developers
- Vala customer success and support
- AI support agents using approved documentation as context

## Information architecture

### Start here

- Welcome to Vala
- Navigating Vala
- Quick start
- Add your first Client

### Ask Vala

- Ask Vala overview
- Sources and citations and reviewing AI answers

### Dashboard

- Dashboard overview and customization

### Contacts

- Contacts overview
- Clients, including the Client record and its Dashboard, Claims, Details, Forms, Documents, Messages, Conditions, Tasks, Relationships, Calendar, and Activity tabs
- Contact views for Representatives, Providers, Organizations, and All Contacts

### Claims

- Claims overview and views
- Claim record Details, Dates, History, and permission-controlled Financials

### Workspaces and tools

- Tasks
- Notes
- Calendar
- Templates, including Documents, Questionnaires, reusable Report templates, and Messages
- Workflows, including Active, Draft, and History
- Calls
- Calculators, including Backpay Calculator and Pension & A&A Calculator

### Account, organization, and resources

- Account settings, Profile, Notifications, and Vala Network
- Organization settings, Team, Roles & permissions, Billing, Integrations, and Security & data handling
- FAQ, Troubleshooting, QuickSubmit, Release Notes, and Contact Support

## Standard page model

Each workflow or feature page should contain only the sections that add value, in this order:

1. **Overview**
2. **When to use it**
3. **Before you begin**
4. **Step-by-step workflow**
5. **Review and verification**
6. **Best practices**
7. **Common issues**
8. **Related workflows**
9. **Walkthrough video**, when required

Pages should explain the customer outcome first, then the interface.

## Page metadata

Every maintained page should eventually include machine-readable metadata in frontmatter or an adjacent manifest.

Example:

```yaml
owner: customer-success
reviewer: product
status: published
product_areas:
  - veterans
  - records
linear_projects:
  - veteran-management
github_paths:
  - apps/web/src/features/veterans
  - services/documents
screenshots:
  - add-veteran
  - upload-records
video: recommended
last_verified: 2026-07-13
```

Required fields:

- `owner`
- `reviewer`
- `status`
- `product_areas`
- `screenshots`
- `video`
- `last_verified`

GitHub and Linear mappings should be added as they are confirmed.

## Dependency model

Documentation dependencies should be explicit.

Example:

```yaml
page: reports
depends_on:
  - veterans
  - records
  - evidence
  - conditions
  - chat
  - forms
```

A change to a dependency does not automatically rewrite every downstream page. It triggers review.

### Initial dependency graph

- **Quick start** depends on organizations, team members, Clients, Documents, Ask Vala, reports, forms, and vSign.
- **Reports** depends on Clients, Documents, Conditions, Ask Vala, and report templates.
- **Forms** depends on Clients, Claims, Conditions, Documents, organization data, and form templates.
- **vSign** depends on forms, recipients, organization settings, and email delivery.
- **Conditions** depends on rating decisions, code sheets, records, AI extraction, and manual review.
- **QuickSubmit** depends on forms, downloaded files, browser support, authentication, and VA submission workflows.

## Documentation impact analysis

Every merged product PR should be evaluated for the following change types:

- User-visible text
- Navigation or information architecture
- Screen layout
- Buttons, fields, menus, or labels
- Workflow order
- Permissions
- Validation rules
- AI behavior or output format
- File compatibility
- Integrations or APIs
- Error states
- Security or data-handling behavior

The impact analysis should produce:

```text
Affected product areas
Affected documentation pages
Screenshots requiring review
Videos requiring review
Release-note recommendation
Confidence level
```

### Review rules

- **Text-only UI change:** review affected page wording and screenshots.
- **Layout change:** regenerate screenshots and review step order.
- **Workflow change:** update all direct and downstream workflow pages.
- **Permission change:** update workflow page, administration page, FAQ, and troubleshooting.
- **AI output change:** update examples, limitations, review guidance, and screenshots.
- **API change:** update reference material, examples, and integration guides.

## Screenshot standards

Screenshots should:

- Use a controlled demo organization and synthetic veteran data.
- Exclude real PII, PHI, claim numbers, email addresses, and customer names.
- Use consistent browser dimensions and zoom.
- Show enough surrounding UI to orient the user.
- Focus on one action or decision per image.
- Use captions that explain why the screen matters.
- Be regenerated after meaningful layout or workflow changes.

Suggested naming:

```text
/images/<product-area>/<workflow>-<step>-<variant>.png
```

## Walkthrough video standards

Create a walkthrough when the workflow:

- Has more than four meaningful steps.
- Includes a non-obvious decision.
- Crosses multiple areas of the product.
- Is commonly covered during onboarding or support.

Default target:

- 60 to 180 seconds
- Task-focused title
- Synthetic data only
- Captions included
- No unnecessary cursor movement or waiting
- Written guide remains the canonical source

A video should be flagged for review when any referenced screen, label, step, permission, or output changes.

## Design system

The help center should visually extend the Vala application.

- **Titles and major headings:** PT Serif, regular weight
- **Body and UI text:** Inter
- **Primary heading color:** near black
- **Accent color:** Vala Orange `#F95B00`
- **Backgrounds:** white and warm off-white
- **Borders:** thin, neutral, and restrained
- **Orange usage:** actions, active states, links, icons, callouts, and selective emphasis

The home page may use a larger orange display title. Standard article H1s should remain near black for readability and hierarchy.

Do not commit or distribute font files. Use supported web-font or platform configuration methods.

## Content style

- Use "veteran" naturally when referring to the person being represented. Use "Client" for an actual Vala interface object, view, button, breadcrumb, or Client record.
- Use the exact current product labels.
- Use **Ask Vala**, **Templates**, **Templates > Questionnaires**, **Workflows**, **History** or **Workflow History**, **Templates > Messages**, and **Calls**. Do not preserve prior labels just because they exist in historical docs.
- Prefer direct instructions.
- Explain review responsibility whenever AI-generated content is involved.
- Do not imply legal advice, guaranteed outcomes, or fully autonomous claim preparation.
- Separate available capabilities from planned capabilities.
- Explain customer outcomes, workflows, verified availability, permissions, review responsibilities, and troubleshooting. Do not document prompts, system prompts, model routing, orchestration, extraction pipelines, proprietary heuristics, confidence mechanics, internal processing architecture, or other engineering details that do not help a customer use Vala.
- Prefer short sections, steps, cards, and examples over dense prose.

## Ownership and review

Recommended ownership:

- **Customer Success:** clarity, onboarding usefulness, support coverage
- **Product:** terminology, workflow correctness, release scope
- **Engineering:** technical behavior, integrations, and implementation mapping
- **Security:** security, privacy, compliance, and data-handling statements
- **AI:** draft generation and impact analysis

No AI-generated documentation should publish directly to `main`. All changes should arrive through a pull request and receive human review.

## Definition of done for customer-visible features

A customer-visible feature is documentation-complete when:

- The relevant Linear issue links to the implementation PR.
- Documentation impact has been assessed.
- Required pages are updated.
- Screenshots are current or explicitly marked pending.
- A walkthrough is updated when required.
- Release notes are drafted when the change is meaningful to customers.
- Product or Customer Success has reviewed the docs change.

## Implementation phases

### Phase 1: Foundation

- Approve navigation and terminology.
- Apply Vala branding.
- Publish core workflow guides.
- Add real screenshots.

### Phase 2: Mapping

- Add page metadata.
- Map documentation pages to product areas, Linear projects, and GitHub paths.
- Create a documentation dependency manifest.

### Phase 3: Impact analysis

- Evaluate merged PRs for documentation impact.
- Open an issue or draft docs PR when review is required.
- Keep publishing human-approved.

### Phase 4: Asset automation

- Use controlled Playwright workflows for screenshots.
- Produce draft walkthrough recordings and narration.
- Flag stale assets based on dependencies.

### Phase 5: Continuous documentation

- Generate draft docs, release notes, support summaries, and customer communications from the same approved change context.
- Measure stale-page rate, time-to-update, support deflection, and onboarding completion.

## Initial success metrics

- Core workflow coverage
- Percentage of customer-visible releases with docs impact assessed
- Median time from product merge to docs PR
- Percentage of screenshots verified within the last 90 days
- Number of onboarding questions answered without live support
- Documentation search success and zero-result queries

## Immediate next actions

1. Review and approve this architecture.
2. Confirm current product terminology and navigation.
3. Verify the Vala brand treatment in the Mintlify preview.
4. Add real application screenshots to the first six guides.
5. Create the first page-to-product dependency manifest.
6. Pilot documentation impact analysis against a small set of recent merged PRs.
