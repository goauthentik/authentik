import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/LicenseNotice";
import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/utils/TimeDeltaHelp";

import { propertyMappingsProvider, propertyMappingsSelector } from "./OAuth2ProviderFormHelpers.js";

import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { clientTypeOptions } from "#admin/providers/oauth2/OAuth2ProviderFormForm";

import {
    FlowDesignationEnum,
    GrantTypeEnum,
    OAuth2DynamicClientRegistration,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const allowedGrantTypeOptions: [GrantTypeEnum, string][] = [
    [GrantTypeEnum.AuthorizationCode, msg("Authorization Code")],
    [GrantTypeEnum.Implicit, msg("Implicit")],
    [GrantTypeEnum.Hybrid, msg("Hybrid")],
    [GrantTypeEnum.RefreshToken, msg("Refresh token")],
    [GrantTypeEnum.ClientCredentials, msg("Client credentials")],
    [GrantTypeEnum.Password, msg("Password")],
    [GrantTypeEnum.UrnIetfParamsOauthGrantTypeDeviceCode, msg("Device-code")],
    [GrantTypeEnum.UrnIetfParamsOauthGrantTypeTokenExchange, msg("Token exchange")],
];

export interface OAuth2DCRFormProps {
    dcr?: Partial<OAuth2DynamicClientRegistration> | null;
}

export function renderForm({ dcr }: OAuth2DCRFormProps) {
    dcr ||= {};
    return html`<ak-license-notice></ak-license-notice>
        <ak-switch-input
            name="createApplication"
            label=${msg("Create application")}
            ?checked=${dcr.createApplication ?? true}
            help=${msg(
                "Automatically create an Application for every client registered through this endpoint.",
            )}
        ></ak-switch-input>
        <ak-text-input
            name="defaultApplicationGroup"
            label=${msg("Default application group")}
            value="${ifDefined(dcr.defaultApplicationGroup)}"
            help=${msg("Group assigned to automatically created applications.")}
        ></ak-text-input>
        <ak-radio-input
            name="defaultClientType"
            label=${msg("Default client type")}
            .options=${clientTypeOptions}
            .value=${dcr.defaultClientType}
        ></ak-radio-input>
        <ak-form-element-horizontal
            label=${msg("Default authorization flow")}
            name="defaultAuthorizationFlow"
        >
            <ak-flow-search
                label=${msg("Default authorization flow")}
                placeholder=${msg("Select an authorization flow...")}
                flowType=${FlowDesignationEnum.Authorization}
                .currentFlow=${dcr.defaultAuthorizationFlow}
            ></ak-flow-search>
            <p class="pf-c-form__helper-text">
                ${msg("Authorization flow applied to dynamically registered clients.")}
            </p>
        </ak-form-element-horizontal>
        <ak-form-element-horizontal
            label=${msg("Default invalidation flow")}
            name="defaultInvalidationFlow"
        >
            <ak-flow-search
                label=${msg("Default invalidation flow")}
                placeholder=${msg("Select an invalidation flow...")}
                flowType=${FlowDesignationEnum.Invalidation}
                .currentFlow=${dcr.defaultInvalidationFlow}
            ></ak-flow-search>
            <p class="pf-c-form__helper-text">
                ${msg("Invalidation flow applied to dynamically registered clients.")}
            </p>
        </ak-form-element-horizontal>
        <ak-form-element-horizontal
            label=${msg("Default property mappings")}
            name="defaultPropertyMappings"
        >
            <ak-dual-select-dynamic-selected
                .provider=${propertyMappingsProvider}
                .selector=${propertyMappingsSelector(dcr.defaultPropertyMappings)}
                available-label=${msg("Available Scopes")}
                selected-label=${msg("Selected Scopes")}
            ></ak-dual-select-dynamic-selected>
            <p class="pf-c-form__helper-text">
                ${msg("Scope mappings applied to dynamically registered clients.")}
            </p>
        </ak-form-element-horizontal>
        <ak-form-group open label=${msg("Advanced settings")}>
            <div class="pf-c-form">
                <ak-text-input
                    name="accessTokenValidity"
                    label=${msg("Access token validity")}
                    value="${dcr.accessTokenValidity ?? "hours=1"}"
                    input-hint="code"
                    required
                    .bighelp=${html`<p class="pf-c-form__helper-text">
                            ${msg("Maximum access token validity for registered clients.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                ></ak-text-input>
                <ak-text-input
                    name="refreshTokenValidity"
                    label=${msg("Refresh token validity")}
                    value="${dcr.refreshTokenValidity ?? "days=30"}"
                    input-hint="code"
                    required
                    .bighelp=${html`<p class="pf-c-form__helper-text">
                            ${msg("Maximum refresh token validity for registered clients.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                ></ak-text-input>
                <ak-form-element-horizontal
                    label=${msg("Allowed grant types")}
                    name="allowedGrantTypes"
                >
                    <ak-checkbox-group
                        name="allowedGrantTypes"
                        .options=${allowedGrantTypeOptions}
                        .value=${dcr.allowedGrantTypes ?? []}
                    ></ak-checkbox-group>
                    <p class="pf-c-form__helper-text">
                        ${msg("If none are selected, all grant types are allowed.")}
                    </p>
                </ak-form-element-horizontal>
                <ak-radio-input
                    name="policyEngineMode"
                    label=${msg("Policy engine mode")}
                    required
                    .options=${policyEngineModes}
                    .value=${dcr.policyEngineMode}
                ></ak-radio-input>
            </div>
        </ak-form-group>`;
}
