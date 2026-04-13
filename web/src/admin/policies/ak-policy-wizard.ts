import "#admin/policies/dummy/DummyPolicyForm";
import "#admin/policies/event_matcher/EventMatcherPolicyForm";
import "#admin/policies/expiry/ExpiryPolicyForm";
import "#admin/policies/expression/ExpressionPolicyForm";
import "#admin/policies/geoip/GeoIPPolicyForm";
import "#admin/policies/password/PasswordPolicyForm";
import "#admin/policies/reputation/ReputationPolicyForm";
import "#admin/policies/unique_password/UniquePasswordPolicyForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { SlottedTemplateResult } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { FormWizardPage } from "#elements/wizard/FormWizardPage";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";

import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";

import { PoliciesApi, Policy, PolicyBinding, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

@customElement("ak-policy-wizard")
export class PolicyWizard extends CreateWizard {
    #api = new PoliciesApi(DEFAULT_CONFIG);

    @property({ type: Boolean })
    public showBindingPage = false;

    @property()
    public bindingTarget: string | null = null;

    public override initialSteps = this.showBindingPage
        ? ["initial", "create-binding"]
        : ["initial"];

    public static override verboseName = msg("Policy");
    public static override verboseNamePlural = msg("Policies");

    public override layout = TypeCreateWizardPageLayouts.list;

    protected apiEndpoint = async (requestInit?: RequestInit): Promise<TypeCreate[]> => {
        return this.#api.policiesAllTypesList(requestInit);
    };

    protected updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("showBindingPage")) {
            this.initialSteps = this.showBindingPage ? ["initial", "create-binding"] : ["initial"];
        }
    }

    protected createBindingActivate = async (page: FormWizardPage) => {
        const createSlot = page.host.steps[1];
        const bindingForm = page.querySelector<PolicyBindingForm>("ak-policy-binding-form");

        if (!bindingForm) return;

        bindingForm.instance = {
            policy: (page.host.state[createSlot] as Policy).pk,
        } as PolicyBinding;
    };

    protected renderForms(): SlottedTemplateResult {
        const bindingPage = this.showBindingPage
            ? html`<ak-wizard-page-form
                  slot="create-binding"
                  headline=${msg("Create Binding")}
                  .activePageCallback=${this.createBindingActivate}
              >
                  <ak-policy-binding-form .targetPk=${this.bindingTarget}></ak-policy-binding-form>
              </ak-wizard-page-form>`
            : null;

        return [super.renderForms(), bindingPage];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-wizard": PolicyWizard;
    }
}
