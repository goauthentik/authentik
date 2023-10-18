import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-tenanted-flow-search";
import { ascii_letters, digits, first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-text-input";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { FlowsInstancesListDesignationEnum, RadiusProvider } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-radius")
export class ApplicationWizardAuthenticationByRadius extends BaseProviderPanel {
    render() {
        const provider = this.wizard.provider as RadiusProvider | undefined;

        return html`<form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(provider?.name)}
                required
            >
            </ak-text-input>

            <ak-form-element-horizontal
                label=${msg("Authentication flow")}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-tenanted-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${provider?.authorizationFlow}
                    .tenantFlow=${rootInterface()?.tenant?.flowAuthentication}
                    required
                ></ak-tenanted-flow-search>
                <p class="pf-c-form__helper-text">${msg("Flow used for users to authenticate.")}</p>
            </ak-form-element-horizontal>

            <ak-form-group expanded>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="sharedSecret"
                        label=${msg("Shared secret")}
                        value=${first(
                            provider?.sharedSecret,
                            randomString(128, ascii_letters + digits),
                        )}
                        required
                    ></ak-text-input>
                    <ak-text-input
                        name="clientNetworks"
                        label=${msg("Client Networks")}
                        value=${first(provider?.clientNetworks, "0.0.0.0/0, ::/0")}
                        required
                        help=${msg(`List of CIDRs (comma-seperated) that clients can connect from. A more specific
                            CIDR will match before a looser one. Clients connecting from a non-specified CIDR
                            will be dropped.`)}
                    ></ak-text-input>
                </div>
            </ak-form-group>
        </form>`;
    }
}

export default ApplicationWizardAuthenticationByRadius;
