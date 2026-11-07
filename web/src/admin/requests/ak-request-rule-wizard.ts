import "#admin/requests/RequestRuleBindingForm";
import "#admin/requests/RequestRuleForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";
import { SlottedTemplateResult } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { FormWizardPage } from "#elements/wizard/FormWizardPage";
import {
    TypeCreateBindChoices,
    TypeCreateWizardPageLayouts,
} from "#elements/wizard/TypeCreateWizardPage";

import { RequestRule, RequestRuleBinding, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { property } from "lit/decorators.js";

const REQUEST_RULE_TYPES: TypeCreate[] = [
    {
        component: "ak-request-rule-form",
        modelName: "requestrule",
        name: msg("Request Rule"),
        description: msg(
            "Define who can approve access requests for the objects this rule is bound to.",
        ),
    },
];

@customElement("ak-request-rule-wizard")
export class AKRequestRuleWizard extends CreateWizard {
    @property({ type: String, useDefault: true })
    public bindingTarget: string | null = null;

    public override initialSteps = ["initial", "create-binding"];

    public static override verboseName = msg("Request Rule");
    public static override verboseNamePlural = msg("Request Rules");

    public override layout = TypeCreateWizardPageLayouts.list;

    public override groupLabel = msg("New Request Rule");
    public override groupDescription = msg("Create a new request rule to bind to this object.");

    protected apiEndpoint = async (): Promise<TypeCreate[]> => {
        return REQUEST_RULE_TYPES;
    };

    protected createBindingActivate = async (
        context: FormWizardPage<{ "create-binding": RequestRule }>,
    ) => {
        const createSlot = context.host.steps[1] as "create-binding";
        const bindingForm = context.querySelector("ak-request-rule-binding-form");

        if (!bindingForm) return;

        if (context.host.state[createSlot]) {
            bindingForm.instance = {
                rule: (context.host.state[createSlot] as RequestRule).uuid,
            } as RequestRuleBinding;
        }
    };

    protected override bindChoices(): TypeCreateBindChoices {
        return {
            label: msg("Existing Request Rule"),
            options: [
                {
                    label: msg("Bind existing rule"),
                    description: msg("Bind an existing request rule to this object."),
                    value: "request-rule",
                },
            ],
        };
    }

    protected renderForms(): SlottedTemplateResult {
        const bindingPage = html`<ak-wizard-page-form
            slot="create-binding"
            headline=${msg("Create Binding")}
            .activePageCallback=${this.createBindingActivate}
        >
            <ak-request-rule-binding-form
                .targetPk=${this.bindingTarget}
            ></ak-request-rule-binding-form>
        </ak-wizard-page-form>`;

        return [super.renderForms(), bindingPage];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-request-rule-wizard": AKRequestRuleWizard;
    }
}
