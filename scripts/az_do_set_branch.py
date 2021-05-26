"""Helper script to get the actual branch name, docker safe"""
import os
from time import time

env_pr_branch = "SYSTEM_PULLREQUEST_SOURCEBRANCH"
default_branch = "BUILD_SOURCEBRANCHNAME"

branch_name = os.environ[default_branch]
if env_pr_branch in os.environ:
    branch_name = os.environ[env_pr_branch].replace("/", "-")

print("##vso[task.setvariable variable=branchName]%s" % branch_name)
print("##vso[task.setvariable variable=timestamp]%s" % int(time()))
