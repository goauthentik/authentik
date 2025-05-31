import "#elements/forms/FormGroup";
import "#admin/applications/wizard/ak-wizard-title";

import { renderForm } from "#admin/providers/scim/SCIMProviderFormForm";

import { PaginatedSCIMMappingList, type SCIMProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

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
