"""Helper script to get the actual branch name, docker safe"""

import configparser
import os
from time import time

parser = configparser.ConfigParser()
parser.read(".bumpversion.cfg")

should_build = str(os.environ.get("DOCKER_USERNAME", None) is not None).lower()

branch_name = os.environ["GITHUB_REF"]
if os.environ.get("GITHUB_HEAD_REF", "") != "":
    branch_name = os.environ["GITHUB_HEAD_REF"]
safe_branch_name = branch_name.replace("refs/heads/", "").replace("/", "-")

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
                f"{name}:latest",
                f"{name}:{version_family}",
            ]
else:
    suffix = ""
    if image_arch and image_arch != "amd64":
        suffix = f"-{image_arch}"
    for name in image_names:
        image_tags += [
            f"{name}:gh-{sha}{suffix}",  # Used for ArgoCD and PR comments
            f"{name}:gh-{safe_branch_name}{suffix}",  # For convenience
            f"{name}:gh-{safe_branch_name}-{int(time())}-{sha[:7]}{suffix}",  # Use by FluxCD
        ]

image_main_tag = image_tags[0]
image_tags_rendered = ",".join(image_tags)

with open(os.environ["GITHUB_OUTPUT"], "a+", encoding="utf-8") as _output:
    print("shouldBuild=%s" % should_build, file=_output)
    print("sha=%s" % sha, file=_output)
    print("version=%s" % version, file=_output)
    print("prerelease=%s" % prerelease, file=_output)
    print("imageTags=%s" % image_tags_rendered, file=_output)
    print("imageMainTag=%s" % image_main_tag, file=_output)
