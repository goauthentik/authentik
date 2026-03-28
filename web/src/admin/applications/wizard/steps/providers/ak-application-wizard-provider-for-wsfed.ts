import "#admin/applications/wizard/ak-wizard-title";
import "#elements/forms/FormGroup";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

import { type AkCryptoCertificateSearch } from "#admin/common/ak-crypto-certificate-search";
import { renderForm } from "#admin/providers/wsfed/WSFederationProviderFormForm";

import { type WSFederationProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

@customElement("ak-application-wizard-provider-for-wsfed")
export class ApplicationWizardProviderWSFedForm extends ApplicationWizardProviderForm<WSFederationProvider> {
    label = msg("Configure WS-Federation Provider");

    @state()
    protected hasSigningKp = false;

    renderForm() {
        const setHasSigningKp = (ev: InputEvent) => {
            const target = ev.target as AkCryptoCertificateSearch;
            if (!target) return;
            this.hasSigningKp = !!target.selectedKeypair;
        };

        return html` <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm({
                    provider: this.wizard.provider as WSFederationProvider,
                    errors: this.wizard.errors?.provider,
                    setHasSigningKp,
                    hasSigningKp: this.hasSigningKp,
                })}
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("WS-Federation Provider Step received uninitialized wizard context.");
        }
        return this.renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-wsfed": ApplicationWizardProviderWSFedForm;
    }
}
