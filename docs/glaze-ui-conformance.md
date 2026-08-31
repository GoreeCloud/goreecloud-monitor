# GoreeCloud Monitor — Glaze UI 2.1 Adoption Candidate

## Status

- Required current Stable design-system release: **Glaze UI 2.1.0**
- Canonical source: `GoreeCloud/goreecloud-glaze-ui`
- Stable release tag: `v2.1.0`
- Stable promotion revision: `c49113eb8b93c267613fdf1bbca1f814495acad7`
- Repository status: **Adoption Candidate**
- Current-Stable conformance claim: **false**
- Production Stable eligibility from this gate: **false**

Monitor now carries a repository-local Glaze UI 2.1 source adoption layer. That source work is migration evidence; it is not a substitute for application-specific rendered, browser/OS accessibility, performance, native/device, or human Visual Excellence acceptance.

The previous 1.0/1.4 source and gate records remain in the repository as historical migration and audit evidence only. They no longer define the active consumer target.

## 2.1 material and interaction mapping

Monitor preserves its successful operational information architecture while adopting the current Stable material hierarchy:

**Canvas → Surface → Soft Glaze → Glaze → Deep Glaze → Live Glaze**

Durable reading and operational content remain solid by default. Glazed material is bounded to navigation, controls, transient interaction, overlays, and live/attention-priority interaction chrome. The migration does not turn monitoring state into decoration and does not replace producer-authoritative service, security, privacy, continuity, identity, or mesh state.

The repository-local 2.1 bridge is `static/monitoring/css/glaze.2.1.css`. Existing `glaze.css`, accessibility, form-factor, staff-administration, and Wardveil presentation layers remain implementation inputs beneath that versioned bridge rather than being falsely relabeled as independently accepted 2.1 implementations.

## Accessibility and density

The 2.1 source layer raises the general effective target floor to **48 CSS pixels** and preserves the **56 CSS pixel** far-view floor. It includes an explicit **56 CSS pixel Touch Assistance** override, an explicit Large Text rendering hook that prevents Compact density from remaining authoritative when readable reflow is required, and Solid material fallbacks for reduced-transparency, increased-contrast, and forced-colors states.

The existing Monitor accessibility layers continue to provide visible focus, reduced-motion behavior, reduced-transparency fallbacks, increased-contrast behavior, forced-colors handling, skip navigation, safe-area-aware composition, and no-backdrop-filter fallbacks.

Source hooks do not prove platform preference detection or complete 200% text reflow. Those behaviors remain acceptance gates and must be verified in representative browser/OS and applicable native contexts before conformance can be claimed.

## Form factors

Monitor retains the existing Mobile, Tablet, Desktop, Wide, and TV/far-view composition foundations while migrating their shared target and density semantics to the 2.1 contract. Width remains only one adaptation signal; supported production contexts must still be validated for actual input method, viewing distance, text scale, focus behavior, safe areas, and task continuity.

## Platform authority boundaries

Glaze UI standardizes presentation only. Monitor continues to treat the following systems as authoritative for their own state:

- **Wardveil Security** for security/protection state and security evidence.
- **Privacy Shield** for privacy-control state and privacy evidence.
- **Everkeep** for continuity/recovery state and evidence.
- **GoreeCloud Identity** for identity/authentication state where integrated.
- **GoreeCloud Mesh** for coordination/connectivity state where integrated.
- **GoreeCloud Notify** for notification-delivery authority where the Monitor producer adapter is used.

A local style, cached value, migration fixture, or simulated state must never be presented as proof that one of these platform systems executed successfully.

## Fail-closed evidence

`docs/glaze-ui-2.1-adoption.json` is the active machine-readable adoption ledger. It pins the exact current Stable release, records source-backed gates, and keeps unresolved gates explicit. `tests/test_glaze_ui_2_1_adoption.py` verifies the source target, exact release provenance, target floors, material hierarchy, accessibility hooks, platform-authority boundary, and fail-closed production posture.

`docs/glaze-ui-1.4-gates.json` remains historical evidence only.

## Remaining acceptance before a current-Stable claim

Monitor must still complete representative rendered task-flow review; browser/OS keyboard, pointer, touch, reduced-motion, reduced-transparency, increased-contrast, forced-colors, 200% Large Text, and Touch Assistance acceptance; application-specific Material Budget/performance evidence; applicable native/package/device acceptance; human Visual Excellence review; and central consumer-registry evidence.

Until those gates are complete, the truthful status is **Glaze UI 2.1 Adoption Candidate**, not `aligned-current-stable` and not production-accepted conformance.
