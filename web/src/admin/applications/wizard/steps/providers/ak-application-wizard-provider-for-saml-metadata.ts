import "#admin/applications/wizard/ak-wizard-title";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

import { createFileMap } from "#elements/utils/inputs";

import { renderForm } from "#admin/providers/saml/SAMLProviderImportFormForm";

import type { ProvidersSamlImportMetadataCreateRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

@customElement("ak-application-wizard-provider-for-saml-metadata")
export class ApplicationWizardProviderSamlMetadataForm extends ApplicationWizardProviderForm<ProvidersSamlImportMetadataCreateRequest> {
    label = msg("Configure SAML Provider from Metadata");

    override get formValues() {
        const data = super.formValues;

        // Get the file input separately since serializeForm doesn't handle files
        const fileMap = createFileMap(this.form?.querySelectorAll("ak-form-element-horizontal"));
        const file = fileMap.get("file");

        if (file) {
            data.file = file;
        }

        return data;
    }

    renderForm() {
        return html`
            <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm(this.wizard.provider)}
            </form>
        `;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("SAML Metadata Provider Step received uninitialized wizard context.");
        }
        return this.renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-saml-metadata": ApplicationWizardProviderSamlMetadataForm;
    }
}
