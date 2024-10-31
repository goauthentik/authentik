import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import { renderForm } from "@goauthentik/admin/providers/saml/SAMLProviderFormForm.js";
import "@goauthentik/elements/forms/FormGroup";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm";

@customElement("ak-application-wizard-provider-for-saml")
export class ApplicationWizardProviderSamlForm extends ApplicationWizardProviderForm<SAMLProvider> {
    @state()
    hasSigningKp = false;

    renderForm() {
        const setHasSigningKp = (ev: InputEvent) => {
            const target = ev.target as AkCryptoCertificateSearch;
            if (!target) return;
            this.hasSigningKp = !!target.selectedKeypair;
        };

        return html` <ak-wizard-title>${msg("Configure SAML Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm(
                    (this.wizard.provider as SAMLProvider) ?? {},
                    this.wizard.errors.provider,
                    setHasSigningKp,
                    this.hasSigningKp,
                )}
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("SAML Provider Step received uninitialized wizard context.");
        }
        return this.renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-saml": ApplicationWizardProviderSamlForm;
    }
}
