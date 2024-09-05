import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { WizardStep } from "@goauthentik/components/ak-wizard-main/AkWizardStep";
import { WizardButton } from "@goauthentik/components/ak-wizard-main/types";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";
import { bound } from "@goauthentik/elements/decorators/bound";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/wizard/TypeCreateWizardPage";
import { TypeCreateWizardPageLayouts } from "@goauthentik/elements/wizard/TypeCreateWizardPage";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

import BasePanel from "../BasePanel";
import type { LocalTypeCreate } from "./ak-application-wizard-authentication-method-choice.choices";
import providerModelsList from "./ak-application-wizard-authentication-method-choice.choices";

export class ProviderMethodStep extends WizardStep {
    id = "provider-method";
    label = msg("Provider Type");
    disabled = false;
    valid = false;

    get buttons(): WizardButton[] {
        return [
            this.valid
                ? { kind: "next", destination: "provider-details" }
                : { kind: "next", disabled: true },
            { kind: "back", destination: "application" },
            { kind: "cancel" },
        ];
    }

    render() {
        // prettier-ignore
        return html`<ak-application-wizard-authentication-method-choice .step=${this}
          ></ak-application-wizard-authentication-method-choice> `;
    }
}

@customElement("ak-application-wizard-authentication-method-choice")
export class ApplicationWizardAuthenticationMethodChoice extends WithLicenseSummary(BasePanel) {
    @bound
    onSelect(ev: CustomEvent<LocalTypeCreate>) {
        this.step.valid = this.valid;
        this.dispatchWizardUpdate({
            update: {
                ...this.wizard,
                providerModel: ev.detail.formName,
                errors: {},
            },
            status: this.valid ? "valid" : "invalid",
        });
    }

    render() {
        const selectedTypes = providerModelsList.filter(
            (t) => t.formName === this.wizard.providerModel,
        );

        // As a hack, the Application wizard has separate provider paths for our three types of
        // proxy providers. This patch swaps the form we want to be directed to on page 3 from the
        // modelName to the formName, so we get the right one.  This information isn't modified
        // or forwarded, so the proxy-plus-subtype is correctly mapped on submission.
        const typesForWizard = providerModelsList.map((provider) => ({
            ...provider,
            modelName: provider.formName,
        }));

        return providerModelsList.length > 0
            ? html`<form class="pf-c-form pf-m-horizontal">
                  <ak-wizard-page-type-create
                      .types=${typesForWizard}
                      layout=${TypeCreateWizardPageLayouts.grid}
                      .selectedType=${selectedTypes.length > 0 ? selectedTypes[0] : undefined}
                      @select=${this.onSelect}
                  ></ak-wizard-page-type-create>
              </form>`
            : html`<ak-empty-state loading header=${msg("Loading")}></ak-empty-state>`;
    }
}

export default ApplicationWizardAuthenticationMethodChoice;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-method-choice": ApplicationWizardAuthenticationMethodChoice;
    }
}
