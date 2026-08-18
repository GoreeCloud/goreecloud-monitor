# GoreeCloud Monitor — Glaze UI 1.0 Conformance

## Status

- Target design system: **Glaze UI 1.0.0**
- Canonical source: `GoreeCloud/glaze-ui`
- Canonical revision reviewed for this implementation: `d6e446fd8ef251259d16368d50aad90d9287a774`
- Automated application contract: `tests/test_glaze_ui.py`
- Production exception: **none approved or required by this source layer**
- Manual visual/accessibility acceptance: **required before Stable classification**

This record describes the Monitor-specific adoption of Glaze UI. It does not fork the design system or make Monitor an authority for shared Glaze tokens.

## Semantic foundation

Monitor uses the canonical Glaze UI semantic roles rather than its former product-local `--bg`, `--surface`, and similar token vocabulary. The implementation includes:

- Canvas atmospheric background.
- Solid and Raised readability/elevation roles.
- Selective Glaze translucency for primary operational surfaces.
- Overlay treatment for compact navigation and attention-priority surfaces.
- Shared semantic text, muted text, line, accent, success, warning, and danger colors.
- Shared spacing, radius, shadow, blur, target-size, focus, and motion semantics.

The Monitor composition remains product-specific. Availability state, incident urgency, recovery state, check latency, and monitoring coverage determine information hierarchy rather than copying another GoreeCloud application's screen layout.

## Product identity

Monitor uses its own pulse/status product mark at `static/monitoring/img/monitor-mark.svg`. The primary shell, authentication surface, and staff administration surface use the same underlying mark, and browser metadata exposes it as the scalable favicon.

The mark is intentionally distinct from the GoreeCloud platform logo and the former generic `G` placeholder while retaining Glaze UI geometry, gradient treatment, depth, and family resemblance.

## Appearance

The primary application supports:

- System appearance by default.
- Explicit Light appearance.
- Explicit Dark appearance.

The preference is browser-local only under `goreecloud-monitor-appearance`. It is not transmitted to Monitor, synchronized to an account, included in analytics, or used for tracking. If browser storage is unavailable, the interface remains functional and falls back to the current session/system appearance. The advanced Django administration surface uses Django's own local theme state while mapping its visual variables to the same Glaze semantic palette; no remote theme service is introduced.

## Adaptive layout

Monitor implements the shared Glaze ranges:

- Compact: up to 599 CSS pixels.
- Medium: 600–1023 CSS pixels.
- Expanded: 1024–1439 CSS pixels.
- Wide: 1440 CSS pixels and above.

Compact primary layouts transform the desktop navigation into a persistent bottom navigation rather than removing navigation. Forms, metrics, filter controls, and history rows reflow for available space instead of merely shrinking desktop geometry. The advanced administration surface also reflows its header, breadcrumbs, forms, and content on narrow displays.

## Accessibility and resilience

The source includes:

- A skip-to-content path in the primary application shell.
- Semantic navigation labels and `aria-current` state.
- Visible `:focus-visible` treatment in both primary and staff-administration surfaces.
- 44-pixel minimum interactive targets.
- Reduced-motion handling.
- Reduced-transparency handling where supported.
- Increased-contrast behavior in the primary application.
- Forced-colors behavior.
- Solid-surface fallbacks when backdrop filtering is unavailable or unsuitable.
- Local/system font and icon behavior with no remote UI, font, icon, analytics, or tracking dependency.

These automated/source guarantees do not replace representative manual keyboard, zoom/reflow, screen-reader, light/dark, contrast, and usability review.

## Monitor-specific surfaces

The Glaze system now covers the complete initial Monitor information architecture:

- Overview.
- Monitors.
- Monitor detail.
- Active and recovered incident history.
- Maintenance.
- Notifications/integration posture.
- Settings.
- Authentication.
- Empty states, forms, filters, status feedback, and destructive/recovery workflows.
- Authenticated staff-only Django administration used for advanced/recovery management.

Normal operation is expected to use the primary Monitor workflows. The framework administration interface remains deliberately staff-only, but its local branding, semantic colors, controls, focus treatment, surfaces, dark/light behavior, translucency fallbacks, and responsive layout are Glaze-aligned so the product no longer contains a default-admin visual island.

## Privacy and security boundary

Visual improvements do not weaken Monitor security controls. The source continues to preserve authentication, staff-only configuration changes, CSRF protection for browser mutations, SSRF-aware target policy, protected environment secrets, least-privilege ntfy publishing, read-only Manager integration, and private-by-default production topology.

The unauthenticated heartbeat acknowledgement is intentionally generic and no longer returns the internal monitor name. The Notifications surface reports configuration posture but never renders the ntfy publisher token or claims operational transition records are delivery receipts.

## Stable-release gate

Automated conformance is necessary but not sufficient for Stable. Before Monitor is classified Stable, representative Compact and Expanded layouts must be reviewed in both light and dark appearance, the staff administration surface must be sampled at representative desktop and compact widths, accessibility/resilience behavior must be exercised on real browser/operating-system combinations, and any discovered visual or interaction defects must be corrected or explicitly documented through the GoreeCloud exception process.
