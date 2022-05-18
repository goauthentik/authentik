import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PoliciesApi, TypeCreate } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/ProxyForm";
import "../../elements/wizard/FormWizardPage";
import "../../elements/wizard/Wizard";
import { WizardPage } from "../../elements/wizard/WizardPage";
import "./dummy/DummyPolicyForm";
import "./event_matcher/EventMatcherPolicyForm";
import "./expiry/ExpiryPolicyForm";
import "./expression/ExpressionPolicyForm";
import "./hibp/HaveIBeenPwnedPolicyForm";
import "./password/PasswordPolicyForm";
import "./reputation/ReputationPolicyForm";

@customElement("ak-policy-wizard-initial")
export class InitialPolicyWizardPage extends WizardPage {
    @property({ attribute: false })
    policyTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, AKGlobal, PFRadio];
    }

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
                            this.host.setSteps(
                                "initial",
                                `type-${type.component}-${type.modelName}`,
                            );
                            this._isValid = true;
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
export class PolicyWizard extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    @property()
    createText = t`Create`;

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
                .steps=${["initial"]}
                header=${t`New policy`}
                description=${t`Create a new policy.`}
            >
                <ak-policy-wizard-initial
                    slot="initial"
                    .sidebarLabel=${() => t`Select type`}
                    .policyTypes=${this.policyTypes}
                >
                </ak-policy-wizard-initial>
                ${this.policyTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            .sidebarLabel=${() => t`Create ${type.name}`}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.createText}</button>
            </ak-wizard>
        `;
    }
}
