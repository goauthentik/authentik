"""Helper script to get the actual branch name, docker safe"""

import configparser
import os
from json import dumps
from time import time

parser = configparser.ConfigParser()
parser.read(".bumpversion.cfg")

# Decide if we should push the image or not
should_push = True
if len(os.environ.get("DOCKER_USERNAME", "")) < 1:
    # Don't push if we don't have DOCKER_USERNAME, i.e. no secrets are available
    should_push = False
if os.environ.get("GITHUB_REPOSITORY").lower() == "goauthentik/authentik-internal":
    # Don't push on the internal repo
    should_push = False

branch_name = os.environ["GITHUB_REF"]
if os.environ.get("GITHUB_HEAD_REF", "") != "":
    branch_name = os.environ["GITHUB_HEAD_REF"]
safe_branch_name = branch_name.replace("refs/heads/", "").replace("/", "-").replace("'", "-")

image_names = os.getenv("IMAGE_NAME").split(",")
image_arch = os.getenv("IMAGE_ARCH") or None

is_pull_request = bool(os.getenv("PR_HEAD_SHA"))
is_release = "dev" not in image_names[0]

sha = os.environ["GITHUB_SHA"] if not is_pull_request else os.getenv("PR_HEAD_SHA")

# 2042.1.0 or 2042.1.0-rc1
version = parser.get("bumpversion", "current_version")
# 2042.1
version_family = ".".join(version.split("-", 1)[0].split(".")[:-1])
prerelease = "-" in version

image_tags = []
if is_release:
    for name in image_names:
        image_tags += [
            f"{name}:{version}",
        ]
        if not prerelease:
            image_tags += [
                f"{name}:{version_family}",
            ]
else:
    suffix = ""
    if image_arch:
        suffix = f"-{image_arch}"
    for name in image_names:
        image_tags += [
            f"{name}:gh-{sha}{suffix}",  # Used for ArgoCD and PR comments
            f"{name}:gh-{safe_branch_name}{suffix}",  # For convenience
            f"{name}:gh-{safe_branch_name}-{int(time())}-{sha[:7]}{suffix}",  # Use by FluxCD
        ]

image_main_tag = image_tags[0].split(":")[-1]


def get_attest_image_names(image_with_tags: list[str]):
    """Attestation only for GHCR"""
    image_tags = []
    for image_name in set(name.split(":")[0] for name in image_with_tags):
        if not image_name.startswith("ghcr.io"):
            continue
        image_tags.append(image_name)
    return ",".join(set(image_tags))


# Generate `cache-to` param
cache_to = ""
if should_push:
    _cache_tag = "buildcache"
    if image_arch:
        _cache_tag += f"-{image_arch}"
    cache_to = f"type=registry,ref={get_attest_image_names(image_tags)}:{_cache_tag},mode=max"


image_build_args = []
if os.getenv("RELEASE", "false").lower() == "true":
    image_build_args = [f"VERSION={os.getenv('REF')}"]
else:
    image_build_args = [f"GIT_BUILD_HASH={sha}"]
image_build_args = "\n".join(image_build_args)

with open(os.environ["GITHUB_OUTPUT"], "a+", encoding="utf-8") as _output:
    print(f"shouldPush={str(should_push).lower()}", file=_output)
    print(f"sha={sha}", file=_output)
    print(f"version={version}", file=_output)
    print(f"prerelease={prerelease}", file=_output)
    print(f"imageTags={','.join(image_tags)}", file=_output)
    print(f"imageTagsJSON={dumps(image_tags)}", file=_output)
    print(f"attestImageNames={get_attest_image_names(image_tags)}", file=_output)
    print(f"imageMainTag={image_main_tag}", file=_output)
    print(f"imageMainName={image_tags[0]}", file=_output)
    print(f"cacheTo={cache_to}", file=_output)
    print(f"imageBuildArgs={image_build_args}", file=_output)
