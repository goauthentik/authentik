import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search";
import { ascii_letters, digits, first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-text-input";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { FlowsInstancesListDesignationEnum, RadiusProvider } from "@goauthentik/api";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

@customElement("ak-application-wizard-provider-for-radius")
export class ApplicationWizardRadiusProviderForm extends WithBrandConfig(
    ApplicationWizardProviderForm<RadiusProvider>,
) {
    label = msg("Configure Radius Provider");

    renderForm(provider: RadiusProvider) {
        return html` <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
            <ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(provider.name)}
                .errorMessages=${this.errorMessages("name")}
                required
            >
            </ak-text-input>

            <ak-form-element-horizontal
                label=${msg("Authentication flow")}
                ?required=${true}
                name="authorizationFlow"
                .errorMessages=${this.errorMessages("authorizationFlow")}
            >
                <ak-branded-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${provider.authorizationFlow}
                    .brandFlow=${this.brand.flowAuthentication}
                    required
                ></ak-branded-flow-search>
                <p class="pf-c-form__helper-text">${msg("Flow used for users to authenticate.")}</p>
            </ak-form-element-horizontal>

            <ak-form-group expanded>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="sharedSecret"
                        label=${msg("Shared secret")}
                        .errorMessages=${this.errorMessages("sharedSecret")}
                        value=${first(
                            provider.sharedSecret,
                            randomString(128, ascii_letters + digits),
                        )}
                        required
                    ></ak-text-input>
                    <ak-text-input
                        name="clientNetworks"
                        label=${msg("Client Networks")}
                        value=${first(provider.clientNetworks, "0.0.0.0/0, ::/0")}
                        .errorMessages=${this.errorMessages("clientNetworks")}
                        required
                        help=${msg(`List of CIDRs (comma-seperated) that clients can connect from. A more specific
                            CIDR will match before a looser one. Clients connecting from a non-specified CIDR
                            will be dropped.`)}
                    ></ak-text-input>
                </div>
            </ak-form-group>
        </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("RAC Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider as RadiusProvider);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-radius": ApplicationWizardRadiusProviderForm;
    }
}
