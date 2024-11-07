import "@goauthentik/admin/applications/wizard/ak-wizard-title";
import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search";
import {
    makeOAuth2PropertyMappingsSelector,
    oauth2PropertyMappingsProvider,
} from "@goauthentik/admin/providers/oauth2/OAuth2PropertyMappings.js";
import {
    clientTypeOptions,
    issuerModeOptions,
    redirectUriHelp,
    subjectModeOptions,
} from "@goauthentik/admin/providers/oauth2/OAuth2ProviderForm";
import {
    IRedirectURIInput,
    akOAuthRedirectURIInput,
} from "@goauthentik/admin/providers/oauth2/OAuth2ProviderRedirectURI";
import {
    makeSourceSelector,
    oauth2SourcesProvider,
} from "@goauthentik/admin/providers/oauth2/OAuth2Sources.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ascii_letters, digits, first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    ClientTypeEnum,
    FlowsInstancesListDesignationEnum,
    MatchingModeEnum,
    RedirectURI,
    SourcesApi,
} from "@goauthentik/api";
import { type OAuth2Provider, type PaginatedOAuthSourceList } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-oauth")
export class ApplicationWizardAuthenticationByOauth extends BaseProviderPanel {
    @state()
    showClientSecret = true;

    @state()
    oauthSources?: PaginatedOAuthSourceList;

    constructor() {
        super();
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
        const errors = this.wizard.errors.provider;

        return html`<ak-wizard-title>${msg("Configure OAuth2/OpenId Provider")}</ak-wizard-title>
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
                    .errorMessages=${errors?.authorizationFlow ?? []}
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
                            @change=${(ev: CustomEvent<{ value: ClientTypeEnum }>) => {
                                this.showClientSecret = ev.detail.value !== ClientTypeEnum.Public;
                            }}
                            .options=${clientTypeOptions}
                        >
                        </ak-radio-input>

                        <ak-text-input
                            name="clientId"
                            label=${msg("Client ID")}
                            value=${provider?.clientId ?? randomString(40, ascii_letters + digits)}
                            .errorMessages=${errors?.clientId ?? []}
                            required
                        >
                        </ak-text-input>

                        <ak-text-input
                            name="clientSecret"
                            label=${msg("Client Secret")}
                            value=${provider?.clientSecret ??
                            randomString(128, ascii_letters + digits)}
                            .errorMessages=${errors?.clientSecret ?? []}
                            ?hidden=${!this.showClientSecret}
                        >
                        </ak-text-input>

                        <ak-form-element-horizontal
                            label=${msg("Redirect URIs/Origins")}
                            required
                            name="redirectUris"
                        >
                            <ak-array-input
                                .items=${[]}
                                .newItem=${() => ({
                                    matchingMode: MatchingModeEnum.Strict,
                                    url: "",
                                })}
                                .row=${(f?: RedirectURI) =>
                                    akOAuthRedirectURIInput({
                                        ".redirectURI": f,
                                        "style": "width: 100%",
                                        "name": "oauth2-redirect-uri",
                                    } as unknown as IRedirectURIInput)}
                            >
                            </ak-array-input>
                            ${redirectUriHelp}
                        </ak-form-element-horizontal>

                        <ak-form-element-horizontal
                            label=${msg("Signing Key")}
                            name="signingKey"
                            .errorMessages=${errors?.signingKey ?? []}
                        >
                            <ak-crypto-certificate-search
                                certificate=${ifDefined(provider?.signingKey ?? nothing)}
                                name="certificate"
                                singleton
                            >
                            </ak-crypto-certificate-search>
                            <p class="pf-c-form__helper-text">
                                ${msg("Key used to sign the tokens.")}
                            </p>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>

                <ak-form-group>
                    <span slot="header"> ${msg("Advanced flow settings")} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-form-element-horizontal
                            name="authenticationFlow"
                            label=${msg("Authentication flow")}
                        >
                            <ak-flow-search
                                flowType=${FlowsInstancesListDesignationEnum.Authentication}
                                .currentFlow=${provider?.authenticationFlow}
                            ></ak-flow-search>
                            <p class="pf-c-form__helper-text">
                                ${msg(
                                    "Flow used when a user access this provider and is not authenticated.",
                                )}
                            </p>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal
                            label=${msg("Invalidation flow")}
                            name="invalidationFlow"
                            required
                        >
                            <ak-flow-search
                                flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                                .currentFlow=${provider?.invalidationFlow}
                                defaultFlowSlug="default-provider-invalidation-flow"
                                required
                            ></ak-flow-search>
                            <p class="pf-c-form__helper-text">
                                ${msg("Flow used when logging out of this provider.")}
                            </p>
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
                            .errorMessages=${errors?.accessCodeValidity ?? []}
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
                            .errorMessages=${errors?.accessTokenValidity ?? []}
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
                            .errorMessages=${errors?.refreshTokenValidity ?? []}
                            ?required=${true}
                            .bighelp=${html` <p class="pf-c-form__helper-text">
                                    ${msg("Configure how long refresh tokens are valid for.")}
                                </p>
                                <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                        >
                        </ak-text-input>

                        <ak-form-element-horizontal
                            label=${msg("Scopes")}
                            name="propertyMappings"
                            .errorMessages=${errors?.propertyMappings ?? []}
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${oauth2PropertyMappingsProvider}
                                .selector=${makeOAuth2PropertyMappingsSelector(
                                    provider?.propertyMappings,
                                )}
                                available-label=${msg("Available Scopes")}
                                selected-label=${msg("Selected Scopes")}
                            ></ak-dual-select-dynamic-selected>
                            <p class="pf-c-form__helper-text">
                                ${msg(
                                    "Select which scopes can be used by the client. The client still has to specify the scope to access the data.",
                                )}
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
                        <ak-switch-input
                            name="includeClaimsInIdToken"
                            label=${msg("Include claims in id_token")}
                            ?checked=${first(provider?.includeClaimsInIdToken, true)}
                            help=${msg(
                                "Include User claims from scopes in the id_token, for applications that don't access the userinfo endpoint.",
                            )}
                        ></ak-switch-input>
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
                            name="jwtFederationSources"
                            .errorMessages=${errors?.jwtFederationSources ?? []}
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${oauth2SourcesProvider}
                                .selector=${makeSourceSelector(provider?.jwtFederationSources)}
                                available-label=${msg("Available Sources")}
                                selected-label=${msg("Selected Sources")}
                            ></ak-dual-select-dynamic-selected>
                            <p class="pf-c-form__helper-text">
                                ${msg(
                                    "JWTs signed by certificates configured in the selected sources can be used to authenticate to this provider.",
                                )}
                            </p>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
            </form>`;
    }
}

export default ApplicationWizardAuthenticationByOauth;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-by-oauth": ApplicationWizardAuthenticationByOauth;
    }
}
