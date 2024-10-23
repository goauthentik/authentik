import "@goauthentik/admin/applications/wizard/ak-wizard-title";
import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search";
import { renderForm } from "@goauthentik/admin/providers/radius/RadiusProviderFormForm.js";
import { ascii_letters, digits, first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-text-input";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import { RadiusProvider } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-radius")
export class ApplicationWizardAuthenticationByRadius extends WithBrandConfig(BaseProviderPanel) {
    render() {
        return html`<ak-wizard-title>${msg("Configure Radius Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                ${renderForm(
                    this.wizard.provider as RadiusProvider | undefined,
                    this.wizard.errors.provider,
                    this.brand,
                )}
            </form>`;
    }
}

export default ApplicationWizardAuthenticationByRadius;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-by-radius": ApplicationWizardAuthenticationByRadius;
    }
}
