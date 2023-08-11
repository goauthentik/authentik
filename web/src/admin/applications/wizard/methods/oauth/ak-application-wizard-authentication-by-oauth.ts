import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-tenanted-flow-search";
import {
    clientTypeOptions,
    issuerModeOptions,
    redirectUriHelp,
    subjectModeOptions,
} from "@goauthentik/admin/providers/oauth2/OAuth2ProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ascii_letters, digits, first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    ClientTypeEnum,
    FlowsInstancesListDesignationEnum,
    PropertymappingsApi,
    SourcesApi,
} from "@goauthentik/api";
import type {
    OAuth2Provider,
    PaginatedOAuthSourceList,
    PaginatedScopeMappingList,
} from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-oauth")
export class ApplicationWizardAuthenticationByOauth extends BaseProviderPanel {
    @state()
    showClientSecret = false;

    @state()
    propertyMappings?: PaginatedScopeMappingList;

    @state()
    oauthSources?: PaginatedOAuthSourceList;

    constructor() {
        super();
        new PropertymappingsApi(DEFAULT_CONFIG)
            .propertymappingsScopeList({
                ordering: "scope_name",
            })
            .then((propertyMappings: PaginatedScopeMappingList) => {
                this.propertyMappings = propertyMappings;
            });

        new SourcesApi(DEFAULT_CONFIG)
            .sourcesOauthList({
                ordering: "name",
                hasJwks: true,
            })
            .then((oauthSources: PaginatedOAuthSourceList) => {
                this.oauthSources = oauthSources;
            });
    }

    render() {
        const provider = this.wizard.provider as OAuth2Provider | undefined;

        return html`<form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(provider?.name)}
                required
            ></ak-text-input>

            <ak-form-element-horizontal
                name="authenticationFlow"
                label=${msg("Authentication flow")}
            >
                <ak-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${provider?.authenticationFlow}
                    required
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when a user access this provider and is not authenticated.")}
                </p>
            </ak-form-element-horizontal>

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

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-radio-input
                        name="clientType"
                        label=${msg("Client type")}
                        .value=${provider?.clientType}
                        required
                        @change=${(ev: CustomEvent<ClientTypeEnum>) => {
                            this.showClientSecret = ev.detail !== ClientTypeEnum.Public;
                        }}
                        .options=${clientTypeOptions}
                    >
                    </ak-radio-input>

                    <ak-text-input
                        name="clientId"
                        label=${msg("Client ID")}
                        value="${first(
                            provider?.clientId,
                            randomString(40, ascii_letters + digits),
                        )}"
                        required
                    >
                    </ak-text-input>

                    <ak-text-input
                        name="clientSecret"
                        label=${msg("Client Secret")}
                        value="${first(
                            provider?.clientSecret,
                            randomString(128, ascii_letters + digits),
                        )}"
                        ?hidden=${!this.showClientSecret}
                    >
                    </ak-text-input>

                    <ak-textarea-input
                        name="redirectUris"
                        label=${msg("Redirect URIs/Origins (RegEx)")}
                        .value=${provider?.redirectUris}
                        .bighelp=${redirectUriHelp}
                    >
                    </ak-textarea-input>

                    <ak-form-element-horizontal label=${msg("Signing Key")} name="signingKey">
                        <ak-crypto-certificate-search
                            certificate=${ifDefined(provider?.signingKey ?? nothing)}
                            name="certificate"
                            singleton
                        >
                        </ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">${msg("Key used to sign the tokens.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header"> ${msg("Advanced protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="accessCodeValidity"
                        label=${msg("Access code validity")}
                        required
                        value="${first(provider?.accessCodeValidity, "minutes=1")}"
                        .bighelp=${html`<p class="pf-c-form__helper-text">
                                ${msg("Configure how long access codes are valid for.")}
                            </p>
                            <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                    >
                    </ak-text-input>

                    <ak-text-input
                        name="accessTokenValidity"
                        label=${msg("Access Token validity")}
                        value="${first(provider?.accessTokenValidity, "minutes=5")}"
                        required
                        .bighelp=${html` <p class="pf-c-form__helper-text">
                                ${msg("Configure how long access tokens are valid for.")}
                            </p>
                            <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                    >
                    </ak-text-input>

                    <ak-text-input
                        name="refreshTokenValidity"
                        label=${msg("Refresh Token validity")}
                        value="${first(provider?.refreshTokenValidity, "days=30")}"
                        ?required=${true}
                        .bighelp=${html` <p class="pf-c-form__helper-text">
                                ${msg("Configure how long refresh tokens are valid for.")}
                            </p>
                            <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                    >
                    </ak-text-input>

                    <ak-form-element-horizontal label=${msg("Scopes")} name="propertyMappings">
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((scope) => {
                                let selected = false;
                                if (!provider?.propertyMappings) {
                                    selected =
                                        scope.managed?.startsWith(
                                            "goauthentik.io/providers/oauth2/scope-",
                                        ) || false;
                                } else {
                                    selected = Array.from(provider?.propertyMappings).some((su) => {
                                        return su == scope.pk;
                                    });
                                }
                                return html`<option
                                    value=${ifDefined(scope.pk)}
                                    ?selected=${selected}
                                >
                                    ${scope.name}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Select which scopes can be used by the client. The client still has to specify the scope to access the data.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>

                    <ak-radio-input
                        name="subMode"
                        label=${msg("Subject mode")}
                        required
                        .options=${subjectModeOptions}
                        .value=${provider?.subMode}
                        help=${msg(
                            "Configure what data should be used as unique User Identifier. For most cases, the default should be fine.",
                        )}
                    >
                    </ak-radio-input>
                    <ak-switch-input name="includeClaimsInIdToken">
                        label=${msg("Include claims in id_token")}
                        ?checked=${first(provider?.includeClaimsInIdToken, true)}
                        help=${msg(
                            "Include User claims from scopes in the id_token, for applications that don't access the userinfo endpoint.",
                        )}></ak-switch-input
                    >
                    <ak-radio-input
                        name="issuerMode"
                        label=${msg("Issuer mode")}
                        required
                        .options=${issuerModeOptions}
                        .value=${provider?.issuerMode}
                        help=${msg(
                            "Configure how the issuer field of the ID Token should be filled.",
                        )}
                    >
                    </ak-radio-input>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header">${msg("Machine-to-Machine authentication settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Trusted OIDC Sources")}
                        name="jwksSources"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.oauthSources?.results.map((source) => {
                                const selected = (provider?.jwksSources || []).some((su) => {
                                    return su == source.pk;
                                });
                                return html`<option value=${source.pk} ?selected=${selected}>
                                    ${source.name} (${source.slug})
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "JWTs signed by certificates configured in the selected sources can be used to authenticate to this provider.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

export default ApplicationWizardAuthenticationByOauth;
