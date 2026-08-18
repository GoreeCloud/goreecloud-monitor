# GoreeCloud Monitor Application Identity

## Role

GoreeCloud Monitor uses one product-specific visual identity across every delivery surface. The canonical artwork is `static/monitoring/img/monitor-mark.svg`, the existing pulse/status Monitor mark. This hardening layer does **not** redraw, regenerate, or replace that artwork. It establishes the existing mark as the authoritative source so future packaging cannot silently introduce unrelated launcher artwork.

## Canonical source

- Product: GoreeCloud Monitor
- Canonical artwork: `static/monitoring/img/monitor-mark.svg`
- Canonical SHA-256: `dcee6c8c70f86bf3fe3ddc9d2a5b33fc1606427433ecf9f24b5d7b155bdb14cf`
- Design language: Glaze UI 1.0
- Security identity: Wardveil Security by GoreeCloud; Wardveil does not replace the Monitor application icon.
- Machine-readable contract: `packaging/app-identity.json`
- Validator: `python scripts/validate_app_identity.py`

The pulse line communicates monitoring/health and the status indicator distinguishes the product by concept, not merely by color. The GoreeCloud platform logo is not used as the Monitor application icon.

## Web

The web shell, login experience, Django administration favicon, browser favicon, and `static/monitoring/manifest.webmanifest` all reference the same canonical Monitor mark. The web manifest uses the scalable SVG directly so browser/platform rasterization remains derived from one source rather than separately maintained artwork.

## Linux AppImage

This repository currently has no Linux desktop client or AppImage packaging pipeline. Therefore it would be inaccurate to claim an AppImage icon is shipped. The identity contract marks this surface `blocked-no-client-package` and requires any future AppImage launcher/package assets to derive from the canonical SVG. A future AppImage release must update the contract to `implemented`, add its packaging path, and pass `python scripts/validate_app_identity.py --require-client-packages` after both client targets exist.

## Android APK/AAB

This repository currently has no Android client or APK/AAB packaging pipeline. Therefore it would be inaccurate to add orphaned launcher resources and call Android supported. The identity contract marks this surface `blocked-no-client-package`. Future Android adaptive/vector/raster launcher variants may adapt platform-required masking and padding, but they must preserve the same underlying pulse/status identity and be traceable to the canonical source.

## Replacement rule

If approved Monitor artwork changes later, replace the canonical source intentionally, update its digest and all derived packaging assets in the same reviewed change, and validate every shipping target. Independent platform redraws or unrelated web/AppImage/APK icons are not acceptable.

## Release boundary

Web identity conformance is source-enforced now. AppImage and Android identity conformance becomes a release gate when those client implementations exist. Client-package absence remains an explicit product-delivery gap rather than a hidden or mocked feature.
