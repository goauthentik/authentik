import "#admin/policies/ak-policy-wizard";
import "#admin/stages/register";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import {
    IconEditButtonByTagName,
    modalInvoker,
    type TransclusionElementConstructor,
} from "#elements/dialogs";
import type { LitPropertyRecord } from "#elements/types";

import { StageBindingForm } from "#admin/flows/StageBindingForm";
import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";

import { DiagramNode, ModelEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";

const bindingForms: Partial<Record<ModelEnum, TransclusionElementConstructor>> = {
    [ModelEnum.AuthentikFlowsFlowstagebinding]: StageBindingForm,
    [ModelEnum.AuthentikPoliciesPolicybinding]: PolicyBindingForm,
};

function iconBindingButton(form: TransclusionElementConstructor, pk: string, item: string) {
    const binding = form.verboseName ?? msg("Binding", { id: "flow-diagram.binding.label" });
    const label = item
        ? msg(str`Edit the ${binding} for ${item}`, {
              id: "flow-diagram.binding.aria-label.labeled",
          })
        : msg(str`Edit the ${binding}`, { id: "flow-diagram.binding.aria-label" });
    return html`<button
        type="button"
        aria-label=${label}
        class="pf-c-button pf-m-plain"
        ${modalInvoker(form, { instancePk: pk } as LitPropertyRecord<HTMLElement>)}
    >
        <pf-tooltip
            position="top"
            content=${msg("Edit Binding", { id: "flow-diagram.binding.tooltip" })}
        >
            <i aria-hidden="true" class="fas fa-link"></i
        ></pf-tooltip>
    </button>`;
}

export function diagramToolbar(node: DiagramNode) {
    const bindingForm = bindingForms[node.bindingModel as ModelEnum];

    // Export both the "Edit Stage/Policy" and "Edit Binding" all in one.
    return html`${IconEditButtonByTagName(node.component, node.pk, node.name)}${bindingForm &&
    node.bindingPk
        ? iconBindingButton(bindingForm, node.bindingPk, node.name)
        : nothing}`;
}
