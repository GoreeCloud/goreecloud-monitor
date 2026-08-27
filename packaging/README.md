# Packaging identity assets

This directory contains source-controlled identity inputs, not standalone client implementations.

GoreeCloud Monitor currently ships as a Django web/API service plus monitoring worker. AppImage and Android client applications have not been approved by the Monitor project specification. The assets here exist so any future approved Linux or Android client starts with the same canonical GoreeCloud Monitor identity used by the web product.

- `appimage/goreecloud-monitor.svg` — Linux/AppImage launcher source.
- `android/res/` — Android adaptive/vector launcher source, including monochrome support.

Do not fork or redraw these assets inside a client repository without updating the canonical identity contract in `docs/product-identity.md`.
