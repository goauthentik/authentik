import "@goauthentik/admin/applications/wizard/ak-wizard-title";
import { renderForm } from "@goauthentik/admin/providers/ldap/LDAPProviderFormForm.js";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

import type { LDAPProvider } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-ldap")
export class ApplicationWizardApplicationDetails extends WithBrandConfig(BaseProviderPanel) {
    render() {
        const provider = this.wizard.provider as LDAPProvider | undefined;
        const errors = this.wizard.errors.provider;

        return html` <ak-wizard-title>${msg("Configure LDAP Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                ${renderForm(provider, errors, this.brand)}
            </form>`;
    }
}

export default ApplicationWizardApplicationDetails;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-by-ldap": ApplicationWizardApplicationDetails;
    }
}
