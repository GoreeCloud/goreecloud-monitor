# GoreeCloud Monitor application identity and native clients

## Status

This document defines the source-controlled application-identity contract and the Linux/Android client acceptance boundary for GoreeCloud Monitor.

The canonical future service origin is **https://monitor.goreecloud.com**. The name is reserved by the Monitor source/project record; this work does not create DNS, Caddy, NetBird, firewall, certificate, or production runtime state.

## Canonical icon authority

The authoritative product artwork is:

`assets/app-icon/goreecloud-monitor.svg`

SHA-256:

`1ef53ba769bdabc37e752b2206e0839845057157406fd416032da461a4132f4b`

The mark combines a Glaze-family rounded layered tile with a high-contrast availability pulse and a distinct healthy-status signal. It contains no visible text, does not depend on remote artwork or fonts, remains recognizable at small sizes, and is intentionally distinct from the GoreeCloud platform logo.

`static/monitoring/img/goreecloud-monitor.svg` must remain byte-identical to the canonical source. `tests/test_app_identity.py` fails if the two copies drift or if the recorded canonical hash no longer matches.

The old `static/monitoring/img/monitor-mark.svg` path is retained temporarily as an identical compatibility copy so previously rendered/cached Monitor pages do not point at unrelated artwork. New source should use `goreecloud-monitor.svg`.

## Web and PWA

The web shell uses the canonical SVG as its favicon and visible product mark. `static/monitoring/manifest.webmanifest` identifies the same scalable source for installable web surfaces. Monitor intentionally does **not** add an offline service worker that caches authenticated operational pages, incident history, or administrative responses.

## Linux and Android

The first-party Tauri 2 shell lives under `clients/goreecloud-monitor/`. It follows the existing GoreeCloud thin-client pattern: the responsive Monitor web application remains the product UI and the server remains the only data/authentication authority.

The client build workflow generates platform-specific launcher assets from the canonical SVG immediately before packaging. Generated icon directories are not source authorities and are excluded from Git.

Expected acceptance artifacts:

- Linux x86_64 AppImage;
- Linux x86_64 Debian package;
- Android ARM64 unsigned/debug APK for device acceptance.

A debug APK is not a Stable mobile release. Stable Android signing requires a separate protected signing/release workflow and real-device acceptance. No private signing key, keystore, password, token, or other signing secret belongs in source control.

## Wardveil client boundary

The native shell is protected by a deliberately narrow Wardveil boundary:

- only `https://monitor.goreecloud.com` on the default HTTPS port and `about:blank` may navigate;
- URL userinfo, HTTP, alternate ports, lookalike hosts, unrelated origins, and new webview windows are denied;
- remote content receives no global Tauri API and no native command/IPC capability;
- denied-navigation diagnostics log only event type, scheme, and hostname;
- no independent native credential store, API token, local monitoring database, or synchronization engine is introduced.

Any future GoreeCloud Identity redirect origin must be added only after the Identity integration contract, CSRF/session behavior, callback path, and navigation policy are explicitly reviewed and tested.

## Glaze UI boundary

The normal client renders the same canonical responsive Monitor web experience, so the complete existing Glaze UI contract remains authoritative. The packaged local fallback is also Glaze-aligned and contains no remote UI dependency. Platform packaging must not replace the primary Monitor experience with framework-default native screens.

## Release and acceptance gates

Source/build success proves that the client packages can be constructed and that their navigation boundary is testable. It does not prove production service reachability, mobile behavior, release signing, desktop integration quality, or manual accessibility/visual acceptance.

Before either native target can be called Stable, validate at minimum:

1. exact-source artifact provenance and checksums;
2. installed launcher identity against the canonical icon;
3. canonical-origin connection over the approved private access path;
4. sign-in/sign-out, session expiry, denied access, and authentication recovery behavior;
5. Overview, monitors, incidents, maintenance, notifications, settings/security role boundaries, and error states;
6. compact/expanded, light/dark, keyboard, zoom/reflow, screen-reader/platform accessibility where applicable;
7. network loss, service-unavailable, certificate failure, and recovery behavior;
8. Android real-device install/upgrade/uninstall and protected release-signing validation;
9. Linux AppImage launch/desktop integration and package removal/reinstall behavior;
10. final Monitor target/live acceptance and explicit production cutover approval.
