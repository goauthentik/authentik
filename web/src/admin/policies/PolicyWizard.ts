import "#admin/policies/dummy/DummyPolicyForm";
import "#admin/policies/event_matcher/EventMatcherPolicyForm";
import "#admin/policies/expiry/ExpiryPolicyForm";
import "#admin/policies/expression/ExpressionPolicyForm";
import "#admin/policies/geoip/GeoIPPolicyForm";
import "#admin/policies/password/PasswordPolicyForm";
import "#admin/policies/reputation/ReputationPolicyForm";
import "#admin/policies/unique_password/UniquePasswordPolicyForm";
import "#admin/forms/ProxyForm";
import "#admin/wizard/FormWizardPage";
import "#admin/wizard/TypeCreateWizardPage";
import "#admin/wizard/Wizard";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";
import { FormWizardPage } from "#admin/wizard/FormWizardPage";
import type { Wizard } from "#admin/wizard/Wizard";

import { PoliciesApi, Policy, PolicyBinding, TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-policy-wizard")
export class PolicyWizard extends AKElement {
    static styles: CSSResult[] = [PFBase, PFButton];

    @property()
    createText = msg("Create");

    @property({ type: Boolean })
    showBindingPage = false;

    @property()
    bindingTarget?: string;

    @property({ attribute: false })
    policyTypes: TypeCreate[] = [];

    @query("ak-wizard")
    wizard?: Wizard;

    firstUpdated(): void {
        new PoliciesApi(DEFAULT_CONFIG).policiesAllTypesList().then((types) => {
            this.policyTypes = types;
        });
    }

    selectListener = ({ detail }: CustomEvent<TypeCreate>) => {
        if (!this.wizard) return;

        const { component, modelName } = detail;
        const idx = this.wizard.steps.indexOf("initial") + 1;

        // Exclude all current steps starting with type-,
        // this happens when the user selects a type and then goes back
        this.wizard.steps = this.wizard.steps.filter((step) => !step.startsWith("type-"));

        this.wizard.steps.splice(idx, 0, `type-${component}-${modelName}`);

        this.wizard.isValid = true;
    };

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${this.showBindingPage ? ["initial", "create-binding"] : ["initial"]}
                header=${msg("New policy")}
                description=${msg("Create a new policy.")}
            >
                <ak-wizard-page-type-create
                    slot="initial"
                    .types=${this.policyTypes}
                    @select=${this.selectListener}
                >
                </ak-wizard-page-type-create>

                ${this.policyTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            label=${msg(str`Create ${type.name}`)}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                ${this.showBindingPage
                    ? html`<ak-wizard-page-form
                          slot="create-binding"
                          label=${msg("Create Binding")}
                          .activePageCallback=${async (context: FormWizardPage) => {
                              const createSlot = context.host.steps[1];
                              const bindingForm =
                                  context.querySelector<PolicyBindingForm>(
                                      "ak-policy-binding-form",
                                  );
                              if (!bindingForm) return;
                              bindingForm.instance = {
                                  policy: (context.host.state[createSlot] as Policy).pk,
                              } as PolicyBinding;
                          }}
                      >
                          <ak-policy-binding-form
                              .targetPk=${this.bindingTarget}
                          ></ak-policy-binding-form>
                      </ak-wizard-page-form>`
                    : nothing}
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.createText}</button>
            </ak-wizard>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-wizard": PolicyWizard;
    }
}
