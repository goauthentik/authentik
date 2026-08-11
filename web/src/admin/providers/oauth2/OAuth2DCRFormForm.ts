import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-radio-input";

import { propertyMappingsProvider, propertyMappingsSelector } from "./OAuth2ProviderFormHelpers.js";

import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { GrantTypeCheckboxItems } from "#admin/providers/oauth2/labels";

import { FlowDesignationEnum, OAuth2DynamicClientRegistration } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export interface OAuth2DCRFormProps {
    dcr?: Partial<OAuth2DynamicClientRegistration> | null;
}

export function renderForm({ dcr }: OAuth2DCRFormProps) {
    dcr ||= {};
    return html`<ak-text-input
            name="defaultApplicationGroup"
            label=${msg("Default application group")}
            value="${ifDefined(dcr.defaultApplicationGroup)}"
            help=${msg("Group assigned to automatically created applications.")}
        ></ak-text-input>
        <ak-form-element-horizontal
            label=${msg("Override authorization flow")}
            name="overrideAuthorizationFlow"
        >
            <ak-flow-search
                label=${msg("Override authorization flow")}
                placeholder=${msg("Select an authorization flow...")}
                flowType=${FlowDesignationEnum.Authorization}
                .currentFlow=${dcr.overrideAuthorizationFlow}
            ></ak-flow-search>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "Authorization flow applied to dynamically registered clients. When not selected, authorization flow of the parent provider is used.",
                )}
            </p>
        </ak-form-element-horizontal>
        <ak-form-element-horizontal
            label=${msg("Override invalidation flow")}
            name="overrideInvalidationFlow"
        >
            <ak-flow-search
                label=${msg("Override invalidation flow")}
                placeholder=${msg("Select an invalidation flow...")}
                flowType=${FlowDesignationEnum.Invalidation}
                .currentFlow=${dcr.overrideInvalidationFlow}
            ></ak-flow-search>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "Invalidation flow applied to dynamically registered clients. When not selected, authorization flow of the parent provider is used.",
                )}
            </p>
        </ak-form-element-horizontal>
        <ak-form-element-horizontal
            label=${msg("Override property mappings")}
            name="overridePropertyMappings"
        >
            <ak-dual-select-dynamic-selected
                .provider=${propertyMappingsProvider}
                .selector=${propertyMappingsSelector(dcr.overridePropertyMappings)}
                available-label=${msg("Available Scopes")}
                selected-label=${msg("Selected Scopes")}
            ></ak-dual-select-dynamic-selected>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "Scope mappings applied to dynamically registered clients. When not selected, scope mappings of the parent provider are used.",
                )}
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
                        .options=${GrantTypeCheckboxItems}
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
