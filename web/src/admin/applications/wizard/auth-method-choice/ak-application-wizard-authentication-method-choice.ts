import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/wizard/TypeCreateWizardPage";
import { TypeCreateWizardPageLayouts } from "@goauthentik/elements/wizard/TypeCreateWizardPage";

import { consume } from "@lit/context";
import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

import BasePanel from "../BasePanel";
import { applicationWizardProvidersContext } from "../ContextIdentity";
import type { LocalTypeCreate } from "./ak-application-wizard-authentication-method-choice.choices";

@customElement("ak-application-wizard-authentication-method-choice")
export class ApplicationWizardAuthenticationMethodChoice extends WithLicenseSummary(BasePanel) {
    @consume({ context: applicationWizardProvidersContext })
    public providerModelsList!: LocalTypeCreate[];

    render() {
        const selectedTypes = this.providerModelsList.filter(
            (t) => t.modelName === this.wizard.providerModel,
        );

        return this.providerModelsList.length > 0
            ? html`<form class="pf-c-form pf-m-horizontal">
                  <ak-wizard-page-type-create
                      .types=${this.providerModelsList}
                      name="selectProviderType"
                      layout=${TypeCreateWizardPageLayouts.grid}
                      .selectedType=${selectedTypes.length > 0 ? selectedTypes[0] : undefined}
                      @select=${(ev: CustomEvent<LocalTypeCreate>) => {
                          this.dispatchWizardUpdate({
                              update: {
                                  ...this.wizard,
                                  providerModel: ev.detail.modelName,
                                  errors: {},
                              },
                              status: this.valid ? "valid" : "invalid",
                          });
                      }}
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
