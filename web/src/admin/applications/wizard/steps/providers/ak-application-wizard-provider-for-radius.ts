import "#admin/applications/wizard/ak-wizard-title";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

import { WithBrandConfig } from "#elements/mixins/branding";

import { ValidationRecord } from "#admin/applications/wizard/types";
import { renderForm } from "#admin/providers/radius/RadiusProviderFormForm";

import { RadiusProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

@customElement("ak-application-wizard-provider-for-radius")
export class ApplicationWizardRadiusProviderForm extends WithBrandConfig(
    ApplicationWizardProviderForm<RadiusProvider>,
) {
    label = msg("Configure Radius Provider");

    renderForm(provider: RadiusProvider, errors: ValidationRecord) {
        return html` <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm({ provider, errors, brand: this.brand })}
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
