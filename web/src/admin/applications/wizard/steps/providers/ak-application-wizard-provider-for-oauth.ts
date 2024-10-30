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
import { html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    ClientTypeEnum,
    FlowsInstancesListDesignationEnum,
    OAuth2ProviderRequest,
    SourcesApi,
} from "@goauthentik/api";
import { type OAuth2Provider, type PaginatedOAuthSourceList } from "@goauthentik/api";

import { ExtendedValidationError } from "../../types.js";
import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

const CLIENT_ID_DEFAULT_LENGTH = 40;
const CLIENT_SECRET_DEFAULT_LENGTH = 128;

@customElement("ak-application-wizard-provider-for-oauth")
export class ApplicationWizardOauth2ProviderForm extends ApplicationWizardProviderForm<OAuth2ProviderRequest> {
    label = msg("Configure Oauth2");

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

    renderForm(provider: OAuth2Provider, errors: ExtendedValidationError) {
        return html`
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                <ak-text-input
                    name="name"
                    label=${msg("Name")}
                    value=${ifDefined(provider.name)}
                    .errorMessages=${this.errorMessages("name")}
                    required
                ></ak-text-input>

                <ak-form-element-horizontal
                    name="authorizationFlow"
                    label=${msg("Authorization flow")}
                    .errorMessages=${this.errorMessages("authorizationFlow")}
                    ?required=${true}
                >
                    <ak-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authorization}
                        .currentFlow=${provider.authorizationFlow}
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
                            .value=${provider.clientType}
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
                            value=${provider.clientId ??
                            randomString(CLIENT_ID_DEFAULT_LENGTH, ascii_letters + digits)}
                            .errorMessages=${this.errorMessages("clientId")}
                            required
                        >
                        </ak-text-input>

                        <ak-text-input
                            name="clientSecret"
                            label=${msg("Client Secret")}
                            value=${provider.clientSecret ??
                            randomString(CLIENT_SECRET_DEFAULT_LENGTH, ascii_letters + digits)}
                            .errorMessages=${this.errorMessages("clientSecret")}
                            ?hidden=${!this.showClientSecret}
                        >
                        </ak-text-input>

                        <ak-textarea-input
                            name="redirectUris"
                            label=${msg("Redirect URIs/Origins (RegEx)")}
                            .value=${provider.redirectUris}
                            .errorMessages=${this.errorMessages("redirectUris")}
                            .bighelp=${redirectUriHelp}
                        >
                        </ak-textarea-input>

                        <ak-form-element-horizontal
                            label=${msg("Signing Key")}
                            name="signingKey"
                            .errorMessages=${this.errorMessages("signingKey")}
                        >
                            <ak-crypto-certificate-search
                                certificate=${ifDefined(provider.signingKey ?? nothing)}
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
                            value="${first(provider.accessCodeValidity, "minutes=1")}"
                            .errorMessages=${this.errorMessages("accessCodeValidity")}
                            .bighelp=${html`<p class="pf-c-form__helper-text">
                                    ${msg("Configure how long access codes are valid for.")}
                                </p>
                                <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                        >
                        </ak-text-input>

                        <ak-text-input
                            name="accessTokenValidity"
                            label=${msg("Access Token validity")}
                            value="${first(provider.accessTokenValidity, "minutes=5")}"
                            required
                            .errorMessages=${this.errorMessages("accessTokenValidity")}
                            .bighelp=${html` <p class="pf-c-form__helper-text">
                                    ${msg("Configure how long access tokens are valid for.")}
                                </p>
                                <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
                        >
                        </ak-text-input>

                        <ak-text-input
                            name="refreshTokenValidity"
                            label=${msg("Refresh Token validity")}
                            value="${first(provider.refreshTokenValidity, "days=30")}"
                            .errorMessages=${this.errorMessages("refreshTokenValidity")}
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
                            .errorMessages=${this.errorMessages("propertyMappings")}
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${oauth2PropertyMappingsProvider}
                                .selector=${makeOAuth2PropertyMappingsSelector(
                                    provider.propertyMappings,
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
                            .value=${provider.subMode}
                            help=${msg(
                                "Configure what data should be used as unique User Identifier. For most cases, the default should be fine.",
                            )}
                        >
                        </ak-radio-input>
                        <ak-switch-input
                            name="includeClaimsInIdToken"
                            label=${msg("Include claims in id_token")}
                            ?checked=${first(provider.includeClaimsInIdToken, true)}
                            help=${msg(
                                "Include User claims from scopes in the id_token, for applications that don't access the userinfo endpoint.",
                            )}
                        ></ak-switch-input>
                        <ak-radio-input
                            name="issuerMode"
                            label=${msg("Issuer mode")}
                            required
                            .options=${issuerModeOptions}
                            .value=${provider.issuerMode}
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
                            .errorMessages=${this.errorMessages("jwksSources")}
                        >
                            <ak-dual-select-dynamic-selected
                                .provider=${oauth2SourcesProvider}
                                .selector=${makeSourceSelector(provider.jwksSources)}
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
            </form>
        `;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("Oauth2 Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider as OAuth2Provider, this.wizard.errors);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-oauth": ApplicationWizardOauth2ProviderForm;
    }
}
