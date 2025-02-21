import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import { renderForm } from "@goauthentik/admin/providers/scim/SCIMProviderFormForm.js";
import "@goauthentik/elements/forms/FormGroup";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import { PaginatedSCIMMappingList, type SCIMProvider } from "@goauthentik/api";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm";

@customElement("ak-application-wizard-provider-for-scim")
export class ApplicationWizardSCIMProvider extends ApplicationWizardProviderForm<SCIMProvider> {
    label = msg("Configure SCIM Provider");

    @state()
    propertyMappings?: PaginatedSCIMMappingList;

    render() {
        return html`<ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm(
                    (this.wizard.provider as SCIMProvider) ?? {},
                    this.wizard.errors.provider,
                )}
            </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-scim": ApplicationWizardSCIMProvider;
    }
}
