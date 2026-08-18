# GoreeCloud Monitor product identity

## Canonical icon

`assets/identity/goreecloud-monitor-icon.svg` is the authoritative application icon for GoreeCloud Monitor.

The symbol is intentionally specific to Monitor: a live availability pulse crosses a Glaze surface while a protected healthy-state indicator remains visually separate from the trace. The product does not reuse the GoreeCloud platform logo and does not depend on color alone for recognition.

## Cross-platform contract

The same underlying identity is carried across the supported and prepared surfaces:

- Web shell and Django administration: `static/monitoring/img/goreecloud-monitor-icon.svg`
- Web favicon representations: 16, 32, 48, 192, and 512 pixel SVG representations under `static/monitoring/img/`
- Browser installation metadata: `static/monitoring/site.webmanifest`
- AppImage/Linux packaging input: `packaging/appimage/goreecloud-monitor.svg`
- Android launcher input: adaptive/vector resources under `packaging/android/res/`

Platform-specific Android masking and monochrome behavior may change padding or rendering, but the pulse/status symbol must not change.

## Delivery boundary

The current GoreeCloud Monitor project specification defines the product as a Django web/API application and monitoring worker. This repository therefore does not claim that an AppImage or APK client exists. The AppImage and Android resources are authoritative packaging inputs so future approved clients cannot invent a separate product identity.

When a native client is approved, its build must consume these source-controlled assets or a deterministic derivative and add build-time validation that rejects icon drift.

## Glaze UI and Wardveil

The application icon belongs to the GoreeCloud Monitor product identity and uses the Glaze UI visual family. Wardveil Security by GoreeCloud remains the platform security/protection identity; Wardveil does not replace the Monitor application icon.

## Change control

Material icon changes require synchronized web, AppImage/Linux, and Android derivatives, conformance-test updates when the identity fingerprint changes, and browser/launcher/small-size/accessibility review on supported clients before Stable classification.
