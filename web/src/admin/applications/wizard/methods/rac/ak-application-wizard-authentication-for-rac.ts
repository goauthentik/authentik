import "@goauthentik/admin/applications/wizard/ak-wizard-title";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import {
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "@goauthentik/admin/providers/rac/RACProviderFormHelpers.js";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { FlowsInstancesListDesignationEnum, RACProvider } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-for-rac")
export class ApplicationWizardAuthenticationByRAC extends BaseProviderPanel {
    render() {
        const provider = this.wizard.provider as RACProvider | undefined;
        const errors = this.wizard.errors.provider;

        return html`<ak-wizard-title
                >${msg("Configure Remote Access Provider Provider")}</ak-wizard-title
            >
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                <ak-text-input
                    name="name"
                    label=${msg("Name")}
                    value=${ifDefined(provider?.name)}
                    .errorMessages=${errors?.name ?? []}
                    required
                ></ak-text-input>

                <ak-form-element-horizontal
                    name="authorizationFlow"
                    label=${msg("Authorization flow")}
                    ?required=${true}
                >
                    <ak-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authorization}
                        .currentFlow=${provider?.authorizationFlow}
                        required
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used when authorizing this provider.")}
                    </p>
                </ak-form-element-horizontal>

                <ak-text-input
                    name="connectionExpiry"
                    label=${msg("Connection expiry")}
                    required
                    value="${provider?.connectionExpiry ?? "hours=8"}"
                    help=${msg(
                        "Determines how long a session lasts before being disconnected and requiring re-authorization.",
                    )}
                ></ak-text-input>

                <ak-form-group .expanded=${true}>
                    <span slot="header"> ${msg("Protocol settings")} </span>
                    <div slot="body" class="pf-c-form">
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
}

export default ApplicationWizardAuthenticationByRAC;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-for-rac": ApplicationWizardAuthenticationByRAC;
    }
}
