import "#admin/common/ak-flow-search/ak-branded-flow-search";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-hidden-text-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { propertyMappingsProvider, propertyMappingsSelector } from "./RadiusProviderFormHelpers.js";

import { ascii_letters, digits, randomString } from "#common/utils";

import {
    CurrentBrand,
    FlowsInstancesListDesignationEnum,
    RadiusProvider,
    ValidationError,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const mfaSupportHelp = msg(
    "When enabled, code-based multi-factor authentication can be used by appending a semicolon and the TOTP code to the password. This should only be enabled if all users that will bind to this provider have a TOTP device configured, as otherwise a password may incorrectly be rejected if it contains a semicolon.",
);

const clientNetworksHelp = msg(
    "List of CIDRs (comma-seperated) that clients can connect from. A more specific CIDR will match before a looser one. Clients connecting from a non-specified CIDR will be dropped.",
);

// All Provider objects have an Authorization flow, but not all providers have an Authentication
// flow. Radius needs only one field, but it is not the Authorization field, it is an
// Authentication field. So, yeah, we're using the authorization field to store the
// authentication information, which is why the ak-branded-flow-search call down there looks so
// weird-- we're looking up Authentication flows, but we're storing them in the Authorization
// field of the target Provider.

export function renderForm(
    provider?: Partial<RadiusProvider>,
    errors: ValidationError = {},
    brand?: CurrentBrand,
) {
    return html`
        <ak-text-input
            name="name"
            label=${msg("Name")}
            placeholder=${msg("Provider name")}
            value=${ifDefined(provider?.name)}
            .errorMessages=${errors?.name}
            required
        >
        </ak-text-input>

        <ak-form-element-horizontal
            label=${msg("Authentication flow")}
            required
            name="authorizationFlow"
            .errorMessages=${errors?.authorizationFlow}
        >
            <ak-branded-flow-search
                label=${msg("Authentication flow")}
                placeholder=${msg("Select an authentication flow...")}
                flowType=${FlowsInstancesListDesignationEnum.Authentication}
                .currentFlow=${provider?.authorizationFlow}
                .brandFlow=${brand?.flowAuthentication}
                required
            ></ak-branded-flow-search>
            <p class="pf-c-form__helper-text">${msg("Flow used for users to authenticate.")}</p>
        </ak-form-element-horizontal>

        <ak-switch-input
            name="mfaSupport"
            label=${msg("Code-based MFA Support")}
            ?checked=${provider?.mfaSupport ?? true}
            help=${mfaSupportHelp}
        >
        </ak-switch-input>

        <ak-form-group open label="${msg("Protocol settings")}">
            <div class="pf-c-form">
                <ak-hidden-text-input
                    name="sharedSecret"
                    label=${msg("Shared secret")}
                    .errorMessages=${errors?.sharedSecret}
                    value=${provider?.sharedSecret ?? randomString(128, ascii_letters + digits)}
                    required
                    input-hint="code"
                ></ak-hidden-text-input>
                <ak-text-input
                    name="clientNetworks"
                    label=${msg("Client Networks")}
                    value=${provider?.clientNetworks ?? "0.0.0.0/0, ::/0"}
                    .errorMessages=${errors?.clientNetworks}
                    required
                    help=${clientNetworksHelp}
                    input-hint="code"
                ></ak-text-input>
                <ak-form-element-horizontal
                    label=${msg("Property mappings")}
                    name="propertyMappings"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(provider?.propertyMappings)}
                        available-label=${msg("Available Property Mappings")}
                        selected-label=${msg("Selected Property Mappings")}
                    ></ak-dual-select-dynamic-selected>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>
        <ak-form-group label="${msg("Advanced flow settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Invalidation flow")}
                    name="invalidationFlow"
                    required
                >
                    <ak-flow-search
                        label=${msg("Invalidation flow")}
                        placeholder=${msg("Select an invalidation flow...")}
                        flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                        .currentFlow=${provider?.invalidationFlow}
                        .errorMessages=${errors?.invalidationFlow}
                        defaultFlowSlug="default-invalidation-flow"
                        required
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used when logging out of this provider.")}
                    </p>
                </ak-form-element-horizontal>
            </div></ak-form-group
        >
    `;
}
