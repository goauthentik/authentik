import "#admin/policies/ak-policy-wizard";
import "#admin/stages/register";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import {
    IconEditButton,
    IconEditButtonByTagName,
    type NamedEntityElementConstructor,
} from "#elements/dialogs";
import { SlottedTemplateResult } from "#elements/types";

import { StageBindingForm } from "#admin/flows/StageBindingForm";
import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";

import { DiagramNode, ModelEnum } from "@goauthentik/api";

type FlowBindingModelEnum =
    | typeof ModelEnum.AuthentikFlowsFlowstagebinding
    | typeof ModelEnum.AuthentikPoliciesPolicybinding;

const BindingForms: Record<FlowBindingModelEnum, NamedEntityElementConstructor> = {
    [ModelEnum.AuthentikFlowsFlowstagebinding]: StageBindingForm,
    [ModelEnum.AuthentikPoliciesPolicybinding]: PolicyBindingForm,
};

function isFlowBindingModelEnum(model: string): model is FlowBindingModelEnum {
    return Object.hasOwn(BindingForms, model);
}

export function diagramToolbar(node: DiagramNode): SlottedTemplateResult {
    if (!isFlowBindingModelEnum(node.bindingModel)) {
        return null;
    }

    const BindingFormConstructor = BindingForms[node.bindingModel];

    const itemName = {
        name: null,
        ariaName: node.name,
    };

    const entityButton = IconEditButtonByTagName(node.component, node.pk, itemName);

    const bindingButton = node.bindingPk
        ? IconEditButton(BindingFormConstructor, node.bindingPk, itemName, { iconName: "fa-link" })
        : null;

    // Export both the "Edit Stage/Policy" and "Edit Binding" all in one.
    return [entityButton, bindingButton];
}
