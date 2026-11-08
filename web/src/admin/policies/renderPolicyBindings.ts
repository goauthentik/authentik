import "#admin/policies/BoundPoliciesList";
import "#elements/cards/SectionCard";
import { PolicyBindingNotice } from "./PolicyBindingForm";

import { PolicyBindingCheckTarget } from "#common/policies/utils";

import { defaultAllowedTypes } from "#admin/policies/BoundPoliciesList";

import { type PolicyEngineMode } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";

interface PolicyBindingProps {
    label?: string;
    description?: string | TemplateResult;
    allowed?: PolicyBindingCheckTarget[];
    target?: string;
    mode?: PolicyEngineMode;
    notices?: PolicyBindingNotice[];
}

export function renderBoundPoliciesExpansion({
    label,
    description,
    allowed,
    target,
    mode,
    notices,
}: PolicyBindingProps) {
    return html`<ak-section-card
        label=${label ?? msg("Policy bindings", { id: "policy-bindings.label" })}
    >
        <ak-bound-policies-list
            .target=${target ?? null}
            .policyEngineMode=${mode ?? ""}
            .allowedTypes=${allowed ?? defaultAllowedTypes}
            .typeNotices=${notices ?? []}
        >
            ${description ? html`<span slot="description">${description}</span>` : null}
        </ak-bound-policies-list>
    </ak-section-card>`;
}
