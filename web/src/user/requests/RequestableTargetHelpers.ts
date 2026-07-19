import { SlottedTemplateResult } from "#elements/types";

import { RequestableTarget } from "@goauthentik/api";

import { html, nothing } from "lit-html";

/**
 * Renders the first of a list of RequestableTargets (an Application or Application
 * Entitlement, paired with its owning Application), plus an overflow count for the rest.
 */
export function renderTargetSummary(targets: RequestableTarget[]): SlottedTemplateResult {
    if (targets.length < 1) {
        return nothing;
    }
    const target = targets[0];
    const overflow = targets.length - 1;
    const label =
        target.label === target.parent.name
            ? target.label
            : `${target.parent.name} / ${target.label}`;
    return html`${label} ${overflow > 0 ? `+${overflow}` : ""}`;
}
