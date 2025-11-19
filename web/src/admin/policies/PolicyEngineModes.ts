import type { RadioOption } from "#elements/forms/Radio";

import { PolicyEngineMode } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export const policyEngineModes: RadioOption<PolicyEngineMode>[] = [
    {
        label: "ANY",
        className: "pf-m-monospace",
        value: PolicyEngineMode.Any,
        default: true,
        description: html`${msg("Any policy must match to grant access")}`,
    },
    {
        label: "ALL",
        className: "pf-m-monospace",
        value: PolicyEngineMode.All,
        description: html`${msg("All policies must match to grant access")}`,
    },
];
