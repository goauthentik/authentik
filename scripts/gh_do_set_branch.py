"""Helper script to get the actual branch name, docker safe"""
import os
from time import time

env_pr_branch = "GITHUB_HEAD_REF"
default_branch = "GITHUB_REF"
sha = "GITHUB_SHA"

branch_name = os.environ[default_branch]
if os.environ.get(env_pr_branch, "") != "":
    branch_name = os.environ[env_pr_branch]
branch_name = branch_name.replace("refs/heads/", "").replace("/", "-")

print("##[set-output name=branchName]%s" % branch_name)
print("##[set-output name=timestamp]%s" % int(time()))
print("##[set-output name=sha]%s" % os.environ[sha])
