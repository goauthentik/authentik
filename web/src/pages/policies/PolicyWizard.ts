import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";

import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";

import { PoliciesApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import { FormWizardStep } from "../../elements/wizard/FormWizardStep";
import { Wizard } from "../../elements/wizard/Wizard";
import { WizardStep } from "../../elements/wizard/WizardStep";
import "./dummy/DummyPolicyForm";
import "./event_matcher/EventMatcherPolicyForm";
import "./expiry/ExpiryPolicyForm";
import "./expression/ExpressionPolicyForm";
import "./hibp/HaveIBeenPwnedPolicyForm";
import "./password/PasswordPolicyForm";
import "./reputation/ReputationPolicyForm";

export class PolicyInitialStep extends WizardStep {
    selected = false;

    isValid(): boolean {
        return this.selected;
    }

    renderNavList(): TemplateResult {
        return html`${t`Select type`}`;
    }

    showDummy = false;

    activeCallback = async () => {
        new PoliciesApi(DEFAULT_CONFIG).policiesAllTypesList().then((types) => {
            this.showDummy =
                types.filter((type) => type.component === "ak-policy-dummy-form").length > 0;
            this.host.requestUpdate();
        });
    };

    render(): TemplateResult {
        return html`${this.showDummy
                ? html`<div class="pf-c-radio">
                      <input
                          class="pf-c-radio__input"
                          type="radio"
                          name="type"
                          id="dummy"
                          @change=${() => {
                              this.host.setSteps(this, new PolicyDummyStep());
                              this.selected = true;
                          }}
                      />
                      <label class="pf-c-radio__label" for="dummy">${t`Dummy`}</label>
                      <span class="pf-c-radio__description"
                          >${t`Policy used for debugging the PolicyEngine. Returns a fixed result,
    but takes a random time to process.`}</span
                      >
                  </div>`
                : html``}
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="event-matcher"
                    @change=${() => {
                        this.host.setSteps(this, new PolicyEventMatcherStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="event-matcher">${t`Event matcher`}</label>
                <span class="pf-c-radio__description"
                    >${t`Passes when Event matches selected criteria.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="expression"
                    @change=${() => {
                        this.host.setSteps(this, new PolicyExpressionStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="expression">${t`Expression`}</label>
                <span class="pf-c-radio__description"
                    >${t`Execute arbitrary Python code to implement custom checks and validation.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="password-expiry"
                    @change=${() => {
                        this.host.setSteps(this, new PolicyPasswordExpiryStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="password-expiry">${t`Password expiry`}</label>
                <span class="pf-c-radio__description"
                    >${t`If password change date is more than x days in the past, invalidate the user's password
    and show a notice.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="hibp"
                    @change=${() => {
                        this.host.setSteps(this, new PolicyHaveIBeenPwnedStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="hibp">${t`Have I been pwned`}</label>
                <span class="pf-c-radio__description"
                    >${t`Check if password is on HaveIBeenPwned's list by uploading the first
    5 characters of the SHA1 Hash.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="password"
                    @change=${() => {
                        this.host.setSteps(this, new PolicyPasswordStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="password">${t`Password`}</label>
                <span class="pf-c-radio__description"
                    >${t`Policy to make sure passwords have certain properties.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="reputation"
                    @change=${() => {
                        this.host.setSteps(this, new PolicyReputationStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="reputation">${t`Reputation`}</label>
                <span class="pf-c-radio__description"
                    >${t`Return true if request IP/target username's score is below a certain threshold.`}</span
                >
            </div> `;
    }
}

class PolicyDummyStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Event matcher policy`}`;
    }
    render(): TemplateResult {
        return html`<ak-policy-dummy-form></ak-policy-dummy-form>`;
    }
}

class PolicyEventMatcherStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Event matcher policy`}`;
    }
    render(): TemplateResult {
        return html`<ak-policy-event-matcher-form></ak-policy-event-matcher-form>`;
    }
}

class PolicyPasswordExpiryStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Password expiry policy`}`;
    }
    render(): TemplateResult {
        return html`<ak-policy-password-expiry-form></ak-policy-password-expiry-form>`;
    }
}

class PolicyExpressionStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Expression policy`}`;
    }
    render(): TemplateResult {
        return html`<ak-policy-expression-form></ak-policy-expression-form>`;
    }
}

class PolicyHaveIBeenPwnedStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Have I been pwned policy`}`;
    }
    render(): TemplateResult {
        return html`<ak-policy-hibp-form></ak-policy-hibp-form>`;
    }
}

class PolicyPasswordStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Password policy`}`;
    }
    render(): TemplateResult {
        return html`<ak-policy-password-form></ak-policy-password-form>`;
    }
}

class PolicyReputationStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Reputation policy`}`;
    }
    render(): TemplateResult {
        return html`<ak-policy-reputation-form></ak-policy-reputation-form>`;
    }
}

@customElement("ak-policy-wizard")
export class PolicyWizard extends Wizard {
    header = t`New policy`;
    description = t`Create a new policy.`;

    steps = [new PolicyInitialStep()];

    static get styles(): CSSResult[] {
        return super.styles.concat(PFRadio);
    }
}
