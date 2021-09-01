"""Helper script to get the actual branch name, docker safe"""
import os
from time import time

env_pr_branch = "GITHUB_HEAD_REF"
default_branch = "GITHUB_REF"

branch_name = os.environ[default_branch]
if env_pr_branch in os.environ:
    branch_name = os.environ[env_pr_branch].replace("refs/heads/", "").replace("/", "-")

print("Debug")
print(os.environ)

print("##[set-output name=branchName]%s" % branch_name)
print("##[set-output name=timestamp]%s" % int(time()))
