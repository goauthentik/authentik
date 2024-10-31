import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import { renderForm } from "@goauthentik/admin/providers/ldap/LDAPProviderFormForm.js";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

import type { LDAPProvider } from "@goauthentik/api";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

@customElement("ak-application-wizard-provider-for-ldap")
export class ApplicationWizardLdapProviderForm extends WithBrandConfig(
    ApplicationWizardProviderForm<LDAPProvider>,
) {
    label = msg("Configure LDAP");

    renderForm(provider: LDAPProvider, errors: ExtendedValidationError) {
        return html`
            <ak-wizard-title>${msg("Configure LDAP Provider")}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm(provider ?? {}, errors, this.brand)}
            </form>
        `;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("LDAP Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider as LDAPProvider);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-ldap": ApplicationWizardLdapProviderForm;
    }
}
