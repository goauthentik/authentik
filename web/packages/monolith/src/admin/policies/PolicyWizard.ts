import { PolicyBindingForm } from "@goauthentik/admin/policies/PolicyBindingForm";
import "@goauthentik/admin/policies/dummy/DummyPolicyForm";
import "@goauthentik/admin/policies/event_matcher/EventMatcherPolicyForm";
import "@goauthentik/admin/policies/expiry/ExpiryPolicyForm";
import "@goauthentik/admin/policies/expression/ExpressionPolicyForm";
import "@goauthentik/admin/policies/password/PasswordPolicyForm";
import "@goauthentik/admin/policies/reputation/ReputationPolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import { FormWizardPage } from "@goauthentik/elements/wizard/FormWizardPage";
import "@goauthentik/elements/wizard/Wizard";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PoliciesApi, Policy, PolicyBinding, TypeCreate } from "@goauthentik/api";

@customElement("ak-policy-wizard-initial")
export class InitialPolicyWizardPage extends WizardPage {
    @property({ attribute: false })
    policyTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, PFRadio];
    }
    sidebarLabel = () => msg("Select type");

    activeCallback: () => Promise<void> = async () => {
        this.host.isValid = false;
        this.shadowRoot
            ?.querySelectorAll<HTMLInputElement>("input[type=radio]")
            .forEach((radio) => {
                if (radio.checked) {
                    radio.dispatchEvent(new CustomEvent("change"));
                }
            });
    };

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.policyTypes.map((type) => {
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${`${type.component}-${type.modelName}`}
                        @change=${() => {
                            const idx = this.host.steps.indexOf("initial") + 1;
                            // Exclude all current steps starting with type-,
                            // this happens when the user selects a type and then goes back
                            this.host.steps = this.host.steps.filter(
                                (step) => !step.startsWith("type-"),
                            );
                            this.host.steps.splice(
                                idx,
                                0,
                                `type-${type.component}-${type.modelName}`,
                            );
                            this.host.isValid = true;
                        }}
                    />
                    <label class="pf-c-radio__label" for=${`${type.component}-${type.modelName}`}
                        >${type.name}</label
                    >
                    <span class="pf-c-radio__description">${type.description}</span>
                </div>`;
            })}
        </form>`;
    }
}

@customElement("ak-policy-wizard")
export class PolicyWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFRadio];
    }

    @property()
    createText = msg("Create");

    @property({ type: Boolean })
    showBindingPage = false;

    @property()
    bindingTarget?: string;

    @property({ attribute: false })
    policyTypes: TypeCreate[] = [];

    firstUpdated(): void {
        new PoliciesApi(DEFAULT_CONFIG).policiesAllTypesList().then((types) => {
            this.policyTypes = types;
        });
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${this.showBindingPage ? ["initial", "create-binding"] : ["initial"]}
                header=${msg("New policy")}
                description=${msg("Create a new policy.")}
            >
                <ak-policy-wizard-initial slot="initial" .policyTypes=${this.policyTypes}>
                </ak-policy-wizard-initial>
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
