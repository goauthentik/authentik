import { SlottedTemplateResult } from "#elements/types";

import { RequestableTarget } from "@goauthentik/api";

import { html, nothing } from "lit-html";

/**
 * Renders the first of a list of RequestableTargets (an Application or Application
 * Entitlement, paired with its owning Application), plus an overflow count for the rest.
 * Shared between AccessRequestListPage (a request's targets) and
 * PolicyBindingModelRequestRuleListPage (a rule's targets) - both represent the same
 * {pbmUuid, label, parent} shape.
 */
export function renderTargetSummary(targets: RequestableTarget[]): SlottedTemplateResult {
    if (targets.length < 1) {
        return nothing;
    }
    const target = targets[0];
    const overflow = targets.length - 1;
    const label = target.parent ? `${target.parent?.name} / ${target.label}` : target.label;
    return html`${label} ${overflow > 0 ? `+${overflow}` : ""}`;
}
