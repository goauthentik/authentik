import { PolicyEngineMode } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export const policyOptions = [
    {
        label: "any",
        value: PolicyEngineMode.Any,
        default: true,
        description: html`${msg("Any policy must match to grant access")}`,
    },
    {
        label: "all",
        value: PolicyEngineMode.All,
        description: html`${msg("All policies must match to grant access")}`,
    },
];
