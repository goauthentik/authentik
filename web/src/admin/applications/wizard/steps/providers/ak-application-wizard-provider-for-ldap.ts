import "#admin/applications/wizard/ak-wizard-title";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

import { WithBrandConfig } from "#elements/mixins/branding";

import { ValidationRecord } from "#admin/applications/wizard/types";
import { renderForm } from "#admin/providers/ldap/LDAPProviderFormForm";

import type { LDAPProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-application-wizard-provider-for-ldap")
export class ApplicationWizardLdapProviderForm extends WithBrandConfig(
    ApplicationWizardProviderForm<LDAPProvider>,
) {
    label = msg("Configure LDAP Provider");

    renderForm(provider: LDAPProvider, errors: ValidationRecord) {
        return html`
            <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm({ provider, errors, brand: this.brand })}
            </form>
        `;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("LDAP Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider, this.wizard.errors.provider ?? {});
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-ldap": ApplicationWizardLdapProviderForm;
    }
}
