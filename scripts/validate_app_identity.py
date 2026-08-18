#!/usr/bin/env python3
"""Fail closed when GoreeCloud Monitor product identity drifts across supported surfaces."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "packaging" / "app-identity.json"


def fail(message: str) -> None:
    raise SystemExit(f"app identity validation failed: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-client-packages", action="store_true", help="also require AppImage and Android package implementations")
    args = parser.parse_args()

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    canonical = contract["canonical_artwork"]
    artwork = ROOT / canonical["path"]
    if not artwork.is_file():
        fail("canonical Monitor artwork is missing")
    digest = hashlib.sha256(artwork.read_bytes()).hexdigest()
    if digest != canonical["sha256"]:
        fail("canonical Monitor artwork digest changed without an identity-contract update")

    shell = (ROOT / "templates" / "monitoring" / "base.html").read_text(encoding="utf-8")
    admin = (ROOT / "templates" / "admin" / "base_site.html").read_text(encoding="utf-8")
    login = (ROOT / "templates" / "registration" / "login.html").read_text(encoding="utf-8")
    for name, source in {"application shell": shell, "administration": admin, "login": login}.items():
        if "monitor-mark.svg" not in source:
            fail(f"{name} does not use the canonical Monitor mark")
    if "manifest.webmanifest" not in shell:
        fail("application shell does not expose the local web-app identity manifest")

    manifest = json.loads((ROOT / contract["surfaces"]["web"]["manifest"]).read_text(encoding="utf-8"))
    if manifest.get("name") != contract["product"]:
        fail("web manifest product name does not match the identity contract")
    icons = manifest.get("icons", [])
    if not icons or not any(icon.get("src", "").endswith("/monitor-mark.svg") and icon.get("type") == "image/svg+xml" for icon in icons):
        fail("web manifest does not derive its icon from the canonical Monitor mark")

    if args.require_client_packages:
        for surface in ("linux_appimage", "android_apk"):
            if contract["surfaces"][surface]["status"] != "implemented":
                fail(f"{surface} is not implemented in this repository")

    print("GoreeCloud Monitor app identity contract validated")


if __name__ == "__main__":
    main()
