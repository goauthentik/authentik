import "#admin/policies/ak-policy-wizard";
import "#admin/stages/register";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import {
    IconEditButton,
    IconEditButtonByTagName,
    type NamedEntityElementConstructor,
} from "#elements/dialogs";

import { StageBindingForm } from "#admin/flows/StageBindingForm";
import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";

import { DiagramNode, ModelEnum } from "@goauthentik/api";

import { html, nothing } from "lit";

const bindingForms: Partial<Record<ModelEnum, NamedEntityElementConstructor>> = {
    [ModelEnum.AuthentikFlowsFlowstagebinding]: StageBindingForm,
    [ModelEnum.AuthentikPoliciesPolicybinding]: PolicyBindingForm,
};

export function diagramToolbar(node: DiagramNode) {
    const bindingForm = bindingForms[node.bindingModel as ModelEnum];

    const itemName = {
        name: null,
        ariaName: node.name,
    };

    const entityButton = IconEditButtonByTagName(node.component, node.pk, itemName);
    const bindingButton =
        bindingForm && node.bindingPk
            ? IconEditButton(bindingForm, node.bindingPk, itemName, { iconName: "fa-link" })
            : nothing;

    // Export both the "Edit Stage/Policy" and "Edit Binding" all in one.
    return html`${entityButton}${bindingButton}`;
}
