import { PolicyBindingForm } from "@goauthentik/admin/policies/PolicyBindingForm";
import "@goauthentik/admin/policies/dummy/DummyPolicyForm";
import "@goauthentik/admin/policies/event_matcher/EventMatcherPolicyForm";
import "@goauthentik/admin/policies/expiry/ExpiryPolicyForm";
import "@goauthentik/admin/policies/expression/ExpressionPolicyForm";
import "@goauthentik/admin/policies/geoip/GeoIPPolicyForm";
import "@goauthentik/admin/policies/password/PasswordPolicyForm";
import "@goauthentik/admin/policies/reputation/ReputationPolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import { FormWizardPage } from "@goauthentik/elements/wizard/FormWizardPage";
import "@goauthentik/elements/wizard/TypeCreateWizardPage";
import "@goauthentik/elements/wizard/Wizard";
import type { Wizard } from "@goauthentik/elements/wizard/Wizard";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PoliciesApi, Policy, PolicyBinding, TypeCreate } from "@goauthentik/api";

@customElement("ak-policy-wizard")
export class PolicyWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

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
                            .sidebarLabel=${() => msg(str`Create ${type.name}`)}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                ${this.showBindingPage
                    ? html`<ak-wizard-page-form
                          slot="create-binding"
                          .sidebarLabel=${() => msg("Create Binding")}
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
                    : html``}
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
