# GoreeCloud Monitor native clients

This directory contains the first-party Tauri 2 shell used to validate Linux AppImage/Debian and Android APK delivery for GoreeCloud Monitor.

## Architecture

The native client is intentionally a thin shell around the canonical private Monitor web service at `https://monitor.goreecloud.com`. Django/PostgreSQL remains the single application, authentication, authorization, monitoring, incident, and configuration authority. The client does not create a second database, offline copy, synchronization engine, native API credential, or alternate authentication system.

The canonical production origin is reserved by source and project documentation but is not published by this client work. Until Monitor is separately deployed and approved at that origin, a built client is an acceptance artifact rather than a production-ready installed client.

## Security boundary

Wardveil Security controls for the shell are intentionally narrow:

- only HTTPS navigation to `monitor.goreecloud.com` on the default HTTPS port is allowed;
- `about:blank` is allowed for webview initialization;
- HTTP, alternate ports, lookalike hosts, arbitrary external origins, and new webview windows are denied;
- `withGlobalTauri` is disabled and no Tauri commands or IPC capabilities are exposed to remote Monitor content;
- navigation-denial logs contain only the event name, scheme, and host, never the path, query, fragment, cookies, or credentials;
- stable Android release signing is not implemented with committed secrets; protected signing material must be supplied through an approved release workflow before Stable APK classification.

Future GoreeCloud Identity/SSO support must be explicitly designed and tested before adding any additional authentication origin. Do not broaden the navigation allowlist preemptively.

## Canonical icon

All native launcher assets are generated from:

`../../assets/app-icon/goreecloud-monitor.svg`

The web application uses an identical source copy verified by automated conformance tests. Do not hand-edit generated Tauri icon files.

## Local validation

From this directory with the pinned Rust toolchain and Tauri CLI available:

```bash
cargo test --manifest-path src-tauri/Cargo.toml
cargo tauri icon ../../assets/app-icon/goreecloud-monitor.svg
cargo tauri build --bundles appimage,deb
```

Android initialization/build requires the Android SDK/NDK and Java 17. CI is the reproducible acceptance path for the unsigned development APK.
