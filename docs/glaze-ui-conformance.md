# GoreeCloud Monitor — Glaze UI 1.5.1 consumer adoption record

## Current authority

The current official Stable GoreeCloud design-system target is **Glaze UI 1.5.1** from `GoreeCloud/goreecloud-glaze-ui`.

Authoritative shared records include:

- `VERSION` = `1.5.1`;
- `GLAZE_UI_V1_5.md`;
- `contracts/v1.5.1/stable-scope.json`;
- `acceptance/v1.5.1-stable.md`;
- `consumers/registry.json`.

The reviewed V1.5 implementation anchor is `ee1032a0822ab8e103f8afe48e5c1859fde65cc9`; the V1.5.1 source-qualification anchor is `5b59d0e36950d737dba35b58ae58058684e0831b`.

Monitor is explicitly listed in the canonical consumer registry as **adoption-required** for 1.5.1.

## Superseded 2.1 record

Monitor previously carried a repository-local "Glaze UI 2.1.0 Adoption Candidate" record and active 2.1-labelled CSS. Current canonical Glaze UI has no authoritative `v2.1.0` Stable scope or acceptance record, and its current Stable authority remains 1.5.1.

The old `docs/glaze-ui-2.1-adoption.json` and `static/monitoring/css/glaze.2.1.css` are therefore historical/non-authoritative migration provenance only. They must not define current consumer state.

## Current source adoption

The active Monitor shell now loads `static/monitoring/css/glaze.1.5.1.css` and declares Glaze UI 1.5.1 as a **source-adoption candidate**.

The browser presentation adapter in `static/monitoring/js/glaze.js` resolves only bounded local presentation context:

- single / stacked / split pane mode from viewport width;
- compact / standard / comfortable control density from viewport and large-text state;
- Solid Accessible material fallback for Reduced Transparency, increased contrast, and Forced Colors;
- Reduced Motion presentation from the browser accessibility preference;
- exact 1.5.1 source identity and presentation-only authority metadata.

The resolver does not infer authorization, grant permission, change monitoring state, execute fallback actions, redefine Wardveil Security/Privacy Shield/Everkeep/Identity/Policy/Observability truth, or manufacture production acceptance.

## Preserved useful source work

Useful material, target-floor, form-factor, and accessibility work from earlier Monitor source remains preserved where compatible:

- 48px ordinary target floor;
- 56px Touch Assistance / far-view floor;
- Canvas → Surface → Soft Glaze → Glaze → Deep Glaze → Live Glaze semantic material vocabulary;
- Reduced Transparency, Reduced Motion, increased contrast, and Forced Colors fallback behavior;
- mobile/tablet/desktop/far-view composition foundations.

These source behaviors still require application-specific acceptance.

## Remaining acceptance

Monitor must remain nonconformant and production-ineligible from this gate until applicable exact-revision evidence exists for:

- representative browser/OS accessibility;
- large-text/reflow behavior;
- representative responsive task continuity;
- application-specific performance budget;
- visual-excellence review;
- known-good rollback;
- governed consumer-registry acceptance;
- production approval.

Shared Glaze UI Stable status never automatically grants Monitor Stable or production status.
