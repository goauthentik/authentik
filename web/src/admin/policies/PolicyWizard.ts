import "@goauthentik/web/admin/policies/dummy/DummyPolicyForm";
import "@goauthentik/web/admin/policies/event_matcher/EventMatcherPolicyForm";
import "@goauthentik/web/admin/policies/expiry/ExpiryPolicyForm";
import "@goauthentik/web/admin/policies/expression/ExpressionPolicyForm";
import "@goauthentik/web/admin/policies/hibp/HaveIBeenPwnedPolicyForm";
import "@goauthentik/web/admin/policies/password/PasswordPolicyForm";
import "@goauthentik/web/admin/policies/reputation/ReputationPolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/web/common/api/config";
import { AKElement } from "@goauthentik/web/elements/Base";
import "@goauthentik/web/elements/forms/ProxyForm";
import "@goauthentik/web/elements/wizard/FormWizardPage";
import "@goauthentik/web/elements/wizard/Wizard";
import { WizardPage } from "@goauthentik/web/elements/wizard/WizardPage";

import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/common/styles/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PoliciesApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-policy-wizard-initial")
export class InitialPolicyWizardPage extends WizardPage {
    @property({ attribute: false })
    policyTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFButton, AKGlobal, PFRadio];
    }
    sidebarLabel = () => t`Select type`;

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
                            this.host.steps = [
                                "initial",
                                `type-${type.component}-${type.modelName}`,
                            ];
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
                <ak-policy-wizard-initial slot="initial" .policyTypes=${this.policyTypes}>
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
