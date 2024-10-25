import AkCryptoCertificateSearch from "@goauthentik/admin/common/ak-crypto-certificate-search";
import { renderForm } from "@goauthentik/admin/providers/saml/SAMLProviderFormForm.js";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import { SAMLProvider } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";
import "./saml-property-mappings-search";

@customElement("ak-application-wizard-authentication-by-saml-configuration")
export class ApplicationWizardProviderSamlConfiguration extends BaseProviderPanel {
    @state()
    hasSigningKp = false;

    render() {
        const setHasSigningKp = (ev: InputEvent) => {
            const target = ev.target as AkCryptoCertificateSearch;
            if (!target) return;
            this.hasSigningKp = !!target.selectedKeypair;
        };

        return html` <ak-wizard-title>${msg("Configure SAML Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                ${renderForm(
                    (this.wizard.provider as SAMLProvider) ?? {},
                    this.wizard.errors.provider,
                    setHasSigningKp,
                    this.hasSigningKp,
                )}
            </form>`;
    }
}

export default ApplicationWizardProviderSamlConfiguration;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-by-saml-configuration": ApplicationWizardProviderSamlConfiguration;
    }
}
