#!/usr/bin/env python3

import asyncio
import json
import os

from conformance import Conformance

CONFORMANCE_SERVER = "https://localhost:8443/"

# This is the name of the Basic OP test plan:
test_plan_name = "oidcc-basic-certification-test-plan"

# This is the variant configuration of the test,
# i.e. static or dynamic metadata location and client registration:
test_variant_config = {"server_metadata": "discovery", "client_registration": "static_client"}

# This is the required configuration for the test run:
test_plan_config = {
    "alias": "authentik",
    "description": "authentik",
    "server": {
        "discoveryUrl": "http://10.120.20.76:9000/application/o/conformance/.well-known/openid-configuration"
    },
    "client": {
        "client_id": "4054d882aff59755f2f279968b97ce8806a926e1",
        "client_secret": "4c7e4933009437fb486b5389d15b173109a0555dc47e0cc0949104f1925bcc6565351cb1dffd7e6818cf074f5bd50c210b565121a7328ee8bd40107fc4bbd867",
    },
    "client_secret_post": {
        "client_id": "4054d882aff59755f2f279968b97ce8806a926e1",
        "client_secret": "4c7e4933009437fb486b5389d15b173109a0555dc47e0cc0949104f1925bcc6565351cb1dffd7e6818cf074f5bd50c210b565121a7328ee8bd40107fc4bbd867",
    },
    "client2": {
        "client_id": "ad64aeaf1efe388ecf4d28fcc537e8de08bcae26",
        "client_secret": "ff2e34a5b04c99acaf7241e25a950e7f6134c86936923d8c698d8f38bd57647750d661069612c0ee55045e29fe06aa101804bdae38e8360647d595e771fea789",
    },
    "consent": {},
    "browser": [
        {
            "match": "http://10.120.20.76:9000/application/o/authorize*",
            "tasks": [
                {
                    "task": "Login",
                    "optional": True,
                    "match": "http://10.120.20.76:9000/if/flow/default-authentication-flow*",
                    "commands": [
                        ["wait", "css", "[name=uid_field]", 10],
                        ["text", "css", "[name=uid_field]", "akadmin"],
                        ["wait", "css", "button[type=submit]", 10],
                        ["click", "css", "button[type=submit]"],
                        ["wait", "css", "[name=password]", 10],
                        ["text", "css", "[name=password]", "foo"],
                        ["click", "css", "button[type=submit]"],
                        ["wait", "css", "#loading-text", 10],
                        ["wait", "contains", "application/o/authorize", 10],
                    ],
                },
                {
                    "task": "Authorize",
                    "match": "http://10.120.20.76:9000/application/o/authorize*",
                },
                {
                    "task": "Authorize 2",
                    "match": "http://10.120.20.76:9000/if/flow/default-provider-authorization-implicit-consent*",
                },
            ],
        }
    ],
}


# Create a Conformance instance...
conformance = Conformance(CONFORMANCE_SERVER, None, verify_ssl=False)

# Create a test plan instance and print the id of it
test_plan = asyncio.run(
    conformance.create_test_plan(test_plan_name, json.dumps(test_plan_config), test_variant_config)
)
plan_id = test_plan["id"]

print(f"----------------\nBegin {test_plan_name}.")
print(f"Plan URL: {CONFORMANCE_SERVER}plan-detail.html?plan={plan_id}\n")

# Iterate over the tests in the plan and run them one by one
for test in test_plan["modules"]:

    # Fetch name and variant of the next test to run
    module_name = test["testModule"]
    variant = test["variant"]
    print(f"Module name: {module_name}")
    print(f"Variant: {json.dumps(variant)}")

    # Create an instance of that test
    module_instance = asyncio.run(
        conformance.create_test_from_plan_with_variant(plan_id, module_name, variant)
    )
    module_id = module_instance["id"]
    print(f"Test URL: {CONFORMANCE_SERVER}log-detail.html?log={module_id}")

    # Run the test and wait for it to finish
    state = asyncio.run(conformance.wait_for_state(module_id, ["FINISHED"]))
    print("")

print(f"Plan URL: {CONFORMANCE_SERVER}plan-detail.html?plan={plan_id}\n")
print(f"\nEnd {test_plan_name}\n----------------")

print("Creating certification package")
asyncio.run(
    conformance.create_certification_package(
        plan_id=plan_id,
        conformance_pdf_path="OpenID-Certification-of-Conformance.pdf",
        output_zip_directory="./zips/",
    )
)
