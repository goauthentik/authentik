import "#components/ak-hidden-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/CodeMirror";
import "#admin/common/ak-license-notice";
import "#components/ak-number-input";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import {
    CompatibilityModeEnum,
    CoreApi,
    CoreGroupsListRequest,
    Group,
    OAuthSource,
    SCIMAuthenticationModeEnum,
    SCIMProvider,
    SourcesApi,
    SourcesOauthListRequest,
    ValidationError,
} from "@goauthentik/api";

import YAML from "yaml";

import {
    groupsProvider,
    groupsSelector,
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "./SCIMProviderFormHelpers.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export function renderAuthToken(provider?: Partial<SCIMProvider>, errors: ValidationError = {}) {
    return html`<ak-hidden-text-input
        name="token"
        label=${msg("Token")}
        value="${provider?.token ?? ""}"
        .errorMessages=${errors?.token}
        required
        help=${msg("Token to authenticate with.")}
        input-hint="code"
    ></ak-hidden-text-input>`;
}

export function renderAuthOAuth(provider?: Partial<SCIMProvider>, _errors: ValidationError = {}) {
    return html`<ak-form-element-horizontal label=${msg("OAuth Source")} name="authOauth">
            <ak-search-select
                .fetchObjects=${async (query?: string): Promise<OAuthSource[]> => {
                    const args: SourcesOauthListRequest = {
                        ordering: "name",
                    };
                    if (query !== undefined) {
                        args.search = query;
                    }
                    const sources = await new SourcesApi(DEFAULT_CONFIG).sourcesOauthList(args);
                    return sources.results;
                }}
                .renderElement=${(source: OAuthSource): string => {
                    return source.name;
                }}
                .value=${(source: OAuthSource | undefined): string | undefined => {
                    return source ? source.pk : undefined;
                }}
                .selected=${(source: OAuthSource): boolean => {
                    return source.pk === provider?.authOauth;
                }}
                blankable
            >
            </ak-search-select>
            <p class="pf-c-form__helper-text">
                ${msg("Specify OAuth source used for authentication.")}
            </p>
        </ak-form-element-horizontal>
        <ak-form-element-horizontal label=${msg("OAuth Parameters")} name="authOauthParams">
            <ak-codemirror mode="yaml" value="${YAML.stringify(provider?.authOauthParams ?? {})}">
            </ak-codemirror>
            <p class="pf-c-form__helper-text">
                ${msg("Additional OAuth parameters, such as grant_type.")}
            </p>
        </ak-form-element-horizontal> `;
}

export function renderAuth(provider?: Partial<SCIMProvider>, errors: ValidationError = {}) {
    switch (provider?.authMode) {
        default:
        case SCIMAuthenticationModeEnum.Token:
            return renderAuthToken(provider, errors);
        case SCIMAuthenticationModeEnum.Oauth:
            return renderAuthOAuth(provider, errors);
    }
}

export interface SCIMProviderFormProps {
    update: () => void;
    provider?: Partial<SCIMProvider>;
    errors?: ValidationError;
}

export function renderForm({ provider = {}, errors = {}, update }: SCIMProviderFormProps) {
    return html`
        <ak-text-input
            name="name"
            value=${ifDefined(provider.name)}
            label=${msg("Provider Name")}
            placeholder=${msg("Type a provider name...")}
            spellcheck="false"
            .errorMessages=${errors.name}
            required
        ></ak-text-input>
        <ak-form-group open label="${msg("Protocol settings")}">
            <div class="pf-c-form">
                <ak-text-input
                    name="url"
                    label=${msg("URL")}
                    value="${provider.url ?? ""}"
                    .errorMessages=${errors.url}
                    required
                    help=${msg("SCIM base url, usually ends in /v2.")}
                    input-hint="code"
                ></ak-text-input>

                <ak-switch-input
                    name="verifyCertificates"
                    label=${msg("Verify SCIM server's certificates")}
                    ?checked=${provider.verifyCertificates ?? true}
                >
                </ak-switch-input>

                <ak-form-element-horizontal
                    label=${msg("Authentication Mode")}
                    required
                    name="authMode"
                >
                    <ak-radio
                        @change=${(ev: CustomEvent<{ value: SCIMAuthenticationModeEnum }>) => {
                            if (!provider) {
                                provider = {};
                            }
                            provider.authMode = ev.detail.value;
                            update();
                        }}
                        .value=${provider?.authMode}
                        .options=${[
                            {
                                label: msg("Token"),
                                value: SCIMAuthenticationModeEnum.Token,
                                default: true,
                                description: html`${msg(
                                    "Authenticate SCIM requests using a static token.",
                                )}`,
                            },
                            {
                                label: msg("OAuth"),
                                value: SCIMAuthenticationModeEnum.Oauth,
                                default: true,
                                description: html`${msg("Authenticate SCIM requests using OAuth.")}
                                    <ak-license-notice></ak-license-notice>`,
                            },
                        ]}
                    ></ak-radio>
                </ak-form-element-horizontal>

                ${renderAuth(provider, errors)}

                <ak-radio-input
                    name="compatibilityMode"
                    label=${msg("Compatibility Mode")}
                    .value=${provider.compatibilityMode}
                    required
                    .options=${[
                        {
                            label: msg("Default"),
                            value: CompatibilityModeEnum.Default,
                            default: true,
                            description: html`${msg("Default behavior.")}`,
                        },
                        {
                            label: msg("AWS"),
                            value: CompatibilityModeEnum.Aws,
                            description: html`${msg(
                                "Altered behavior for usage with Amazon Web Services.",
                            )}`,
                        },
                        {
                            label: msg("Slack"),
                            value: CompatibilityModeEnum.Slack,
                            description: html`${msg("Altered behavior for usage with Slack.")}`,
                        },
                        {
                            label: msg("Salesforce"),
                            value: CompatibilityModeEnum.Sfdc,
                            description: html`${msg("Altered behavior for usage with Salesforce.")}`,
                        },
                    ]}
                    help=${msg(
                        "Alter authentik's behavior for vendor-specific SCIM implementations.",
                    )}
                ></ak-radio-input>
                <ak-text-input
                    name="serviceProviderConfigCacheTimeout"
                    label=${msg("Service Provider Config cache timeout")}
                    input-hint="code"
                    required
                    value="${provider.serviceProviderConfigCacheTimeout ?? "hours=1"}"
                    .errorMessages=${errors.service_provider_config_cache_timeout}
                    .bighelp=${html`<p class="pf-c-form__helper-text">
                            ${msg(
                                "Cache duration for ServiceProviderConfig responses. Set minutes=0 to disable caching.",
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                >
                </ak-text-input>
                <ak-switch-input
                    name="dryRun"
                    label=${msg("Enable dry-run mode")}
                    ?checked=${provider.dryRun ?? false}
                    help=${msg(
                        "When enabled, mutating requests will be dropped and logged instead.",
                    )}
                ></ak-switch-input>
            </div>
        </ak-form-group>
        <ak-form-group open label="${msg("User filtering")}">
            <div class="pf-c-form">
                <ak-switch-input
                    name="excludeUsersServiceAccount"
                    label=${msg("Exclude service accounts")}
                    ?checked=${provider.excludeUsersServiceAccount ?? true}
                >
                </ak-switch-input>

                <ak-form-element-horizontal label=${msg("Group Filter")} name="groupFilters">
                    <ak-dual-select-dynamic-selected
                        .provider=${groupsProvider}
                        .selector=${groupsSelector(provider?.groupFilters, null)}
                        available-label=${msg("Available Groups")}
                        selected-label=${msg("Selected Groups")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg("Groups to be synced. If empty, all groups will be synced.")}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>

        <ak-form-group open label="${msg("Attribute mapping")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("User Property Mappings")}
                    name="propertyMappings"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(
                            provider.propertyMappings,
                            "goauthentik.io/providers/scim/user",
                        )}
                        available-label=${msg("Available User Property Mappings")}
                        selected-label=${msg("Selected User Property Mappings")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg("Property mappings used to user mapping.")}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Group Property Mappings")}
                    name="propertyMappingsGroup"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(
                            provider.propertyMappingsGroup,
                            "goauthentik.io/providers/scim/group",
                        )}
                        available-label=${msg("Available Group Property Mappings")}
                        selected-label=${msg("Selected Group Property Mappings")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg("Property mappings used to group creation.")}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>

        <ak-form-group label="${msg("Sync settings")}">
            <div class="pf-c-form">
                <ak-number-input
                    label=${msg("Page size")}
                    required
                    name="pageSize"
                    value="${provider.syncPageSize ?? 100}"
                    help=${msg("Controls the number of objects synced in a single task.")}
                ></ak-number-input>
                <ak-text-input
                    name="syncPageTimeout"
                    label=${msg("Page timeout")}
                    input-hint="code"
                    required
                    value="${provider.syncPageTimeout ?? "minutes=30"}"
                    .bighelp=${html`<p class="pf-c-form__helper-text">
                            ${msg("Timeout for synchronization of a single page.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                >
                </ak-text-input>
            </div>
        </ak-form-group>
    `;
}
