#!/usr/bin/env python3
# Copyright 2025 Merlin Zimmerman
# License: MIT
import json
import sys
import tomllib
import urllib.request

FREE_THREADING_CLASSIFIER = "Programming Language :: Python :: Free Threading"
IGNORE_PACKAGES = [
    "ak-guardian",
    "authentik",
    "django-channels-postgres",
    "django-dramatiq-postgres",
    "django-postgres-cache",
    "pywin32",
]


def load_toml(path: str):
    with open(path, "rb") as f:
        return tomllib.load(f)


def extract_packages(lock):
    """
    Supports both uv v1 and v2 lock formats.
    Returns a dict {name: version}
    """
    if lock.get("version", None) != 1 or lock.get("revision", None) != 3:
        raise ValueError("Unsupported uv.lock version/revision")
    packages = lock.get("package", [])
    if not isinstance(packages, list):
        raise ValueError("Invalid uv.lock format: 'package' should be a list")
    return {pkg["name"]: pkg["version"] for pkg in packages}


def fetch_metadata_from_pypi(name: str, version: str):
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)


def main():
    pyproject = load_toml("pyproject.toml")
    overrides = pyproject.get("tool", {}).get("free-threading-check", {}).get("overrides", {})
    lock = load_toml("uv.lock")
    packages = extract_packages(lock)

    print(f"Found {len(packages)} packages in uv.lock\n")

    missing_support = []

    all_support = True
    for name, version in packages.items():
        print(f"Checking {name}=={version} ...", end="", flush=True)
        if name in IGNORE_PACKAGES:
            continue
        if name in overrides:
            if overrides[name]:
                print(" ok (overridden to True)")
            else:
                missing_support.append(name)
                all_support = False
                print(" \033[91mMISSING (overridden to False)\033[0m")
            continue
        try:
            data = fetch_metadata_from_pypi(name, version)
        except Exception as e:
            print(f" \033[91mERROR fetching metadata: {e}\033[0m")
            all_support = False
            continue
        supports = False
        classifiers = data.get("info", {}).get("classifiers", [])
        for classifier in classifiers:
            if classifier.startswith(FREE_THREADING_CLASSIFIER):
                print(" ok (declared in classifiers)")
                supports = True
                break
        if not supports:
            all_abi_are_none = True
            # Thanks https://github.com/hugovk/free-threaded-wheels/blob/26caec3cebe8bbd2bdfb98ceefe73a93a28ff36f/utils.py#L43-L56
            for download in data["urls"]:
                if download["packagetype"] == "bdist_wheel":
                    abi_tag = download["filename"].removesuffix(".whl").split("-")[-2]
                    if abi_tag != "none":
                        all_abi_are_none = False
                    if abi_tag.endswith("t") and abi_tag.startswith("cp31"):
                        print(" ok (found free-threaded wheel)")
                        supports = True
                        break
            if all_abi_are_none:
                print(" ok (all wheels are abi 'none')")
                supports = True
        if not supports:
            missing_support.append(name)
            all_support = False
            print(" \033[91mMISSING\033[0m")
    if all_support:
        print("\n\033[92mAll packages support free-threading!\033[0m")
    else:
        print("\n\033[91mSome packages are missing free-threading support.\033[0m")
        print(*missing_support, sep="\n")
    print("\nDone.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(1)
