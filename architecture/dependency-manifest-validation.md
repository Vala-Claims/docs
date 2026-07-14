# Documentation Dependency Manifest Validation

This report tests the initial dependency manifest against three shipped product changes in `Vala-Claims/vala`.

## Test 1: PR #812, refresh signing packet PDFs on resend

### Product areas changed
- vSign delivery behavior
- Staff signing review
- Client portal signing
- PDF packet composition

### Manifest result
Flagged pages:
- `core-workflows/forms-and-vsign.mdx`
- `getting-started/quickstart.mdx`

Required review:
- Text accuracy
- Staff review/send screenshots
- Client signing screenshots
- Forms and vSign walkthrough

### Assessment
Correct. The behavior changed without a major navigation redesign, so the primary need is to explain that edits made before signing are reflected when a packet is resent, while signed or partially signed packets are protected from recomposition.

## Test 2: PR #782, primary point of contact and relaxed phone uniqueness

### Product areas changed
- Veteran profile
- Relationships
- Primary point of contact selection
- Form generation
- vSign recipient selection
- Single and multi-document send dialogs

### Manifest result
Flagged pages:
- `core-workflows/veterans.mdx`
- `core-workflows/forms-and-vsign.mdx`
- `getting-started/quickstart.mdx`

Required review:
- Text update
- Veteran details screenshots
- Relationships screenshots
- Send-dialog screenshots
- Quick-start workflow review

### Assessment
Correct. This is a strong example of a dependency-driven change. A control introduced on the veteran record changes downstream form population and signing behavior, so updating only the Veterans page would leave the workflow docs incomplete.

## Test 3: PR #493, multi-document vSign envelopes

### Product areas changed
- Forms workflow
- Staff signing review
- Client portal
- Packet grouping
- Field identity across attachments
- Automations

### Manifest result
Flagged pages:
- `core-workflows/forms-and-vsign.mdx`
- `getting-started/quickstart.mdx`

Required review:
- Major text update
- New packet-building screenshots
- New staff review screenshots
- New client signing screenshots
- Replacement walkthrough video

### Assessment
Correct. This is a major workflow change and should invalidate both written steps and walkthrough assets.

## Initial conclusions

The manifest successfully distinguishes among:

1. Direct page impact, such as vSign UI changes affecting Forms and vSign.
2. Downstream workflow impact, such as primary point of contact affecting generated forms and signer selection.
3. Asset invalidation, where text, screenshots, and walkthrough videos require different review levels.

## Gaps found

The next version should add mappings for:
- Conditions
- Evidence and source citations
- Timeline
- Tasks and automations
- Organization administration and permissions
- Calls and transcription
- QuickSubmit and browser extensions
- Community Edition and plan-based feature visibility
- Billing and usage limits

## Recommended implementation sequence

1. Expand the manifest to all current customer-facing sections.
2. Add stable feature identifiers to Linear issues and PR templates.
3. Build a script that compares changed product paths against this manifest.
4. Post a documentation impact summary on each product PR.
5. Open a docs PR only when the impact summary identifies required changes.
6. Add screenshot and walkthrough regeneration after text-impact detection is trusted.
