#!/usr/bin/env python3

import yaml

with open("template.yaml") as file:
    template = yaml.safe_load(file)
    del template["Conditions"]["CDKMetadataAvailable"]
    del template["Parameters"]["BootstrapVersion"]
    del template["Resources"]["CDKMetadata"]
with open("template.yaml", "w") as file:
    yaml.dump(template, file)
