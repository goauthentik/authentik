import "#components/ak-text-input";
import "#elements/CodeMirror";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import { ApplicationWizardProviderForm } from "#admin/applications/wizard/steps/providers/ApplicationWizardProviderForm";
import { AKAuthorizationFlowField } from "#admin/providers/components/flow-fields";
import {
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "#admin/providers/rac/RACProviderFormHelpers";

import { type RACProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-application-wizard-provider-for-rac")
export class ApplicationWizardRACProviderForm extends ApplicationWizardProviderForm<RACProvider> {
    label = msg("Configure Remote Access Provider");

    renderForm(provider: RACProvider) {
        return html`<h3 class="pf-c-wizard__main-title">${this.label}</h3>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                <ak-text-input
                    name="name"
                    label=${msg("Name")}
                    value=${ifDefined(provider.name)}
                    .errorMessages=${this.errorMessages("name")}
                    required
                ></ak-text-input>

                ${AKAuthorizationFlowField({ value: provider.authorizationFlow })}

                <ak-text-input
                    name="connectionExpiry"
                    label=${msg("Connection expiry")}
                    required
                    value="${provider.connectionExpiry ?? "hours=8"}"
                    help=${msg(
                        "Determines how long a session lasts before being disconnected and requiring re-authorization.",
                    )}
                    input-hint="code"
                ></ak-text-input>

                <ak-form-group open label="${msg("Protocol settings")}">
                    <div class="pf-c-form">
                        <ak-form-element-horizontal
                            label=${msg("Property mappings")}
                            name="propertyMappings"
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${propertyMappingsProvider}
                                .selector=${propertyMappingsSelector(provider?.propertyMappings)}
                                available-label="${msg("Available Property Mappings")}"
                                selected-label="${msg("Selected Property Mappings")}"
                            ></ak-dual-select-dynamic-selected>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("RAC Provider Step received uninitialized wizard context.");
        }

        return this.renderForm(this.wizard.provider);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-rac": ApplicationWizardRACProviderForm;
    }
}
