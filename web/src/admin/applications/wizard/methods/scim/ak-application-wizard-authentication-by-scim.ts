import { renderForm } from "@goauthentik/admin/providers/scim/SCIMProviderFormForm.js";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import { PaginatedSCIMMappingList, type SCIMProvider } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-scim")
export class ApplicationWizardAuthenticationBySCIM extends BaseProviderPanel {
    @state()
    propertyMappings?: PaginatedSCIMMappingList;

    constructor() {
        super();
    }

    render() {
        return html`<ak-wizard-title>${msg("Configure SCIM Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                ${renderForm(
                    (this.wizard.provider as SCIMProvider) ?? {},
                    this.wizard.errors.provider,
                )}
            </form>`;
    }
}

export default ApplicationWizardAuthenticationBySCIM;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-by-scim": ApplicationWizardAuthenticationBySCIM;
    }
}
