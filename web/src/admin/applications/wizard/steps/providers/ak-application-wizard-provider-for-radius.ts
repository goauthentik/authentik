import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import { ValidationRecord } from "@goauthentik/admin/applications/wizard/types";
import { renderForm } from "@goauthentik/admin/providers/radius/RadiusProviderFormForm.js";
import { WithBrandConfig } from "@goauthentik/elements/mixins/brand";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import { RadiusProvider } from "@goauthentik/api";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

@customElement("ak-application-wizard-provider-for-radius")
export class ApplicationWizardRadiusProviderForm extends WithBrandConfig(
    ApplicationWizardProviderForm<RadiusProvider>,
) {
    label = msg("Configure Radius Provider");

    renderForm(provider: RadiusProvider, errors: ValidationRecord) {
        return html` <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm(provider ?? {}, errors, this.brand)}
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("RAC Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(
            this.wizard.provider as RadiusProvider,
            this.wizard.errors?.provider ?? {},
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-radius": ApplicationWizardRadiusProviderForm;
    }
}
