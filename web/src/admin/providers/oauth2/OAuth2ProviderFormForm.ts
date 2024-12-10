import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import {
    IRedirectURIInput,
    akOAuthRedirectURIInput,
} from "@goauthentik/admin/providers/oauth2/OAuth2ProviderRedirectURI";
import { ascii_letters, digits, first, randomString } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/elements/ak-array-input.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    ClientTypeEnum,
    FlowsInstancesListDesignationEnum,
    IssuerModeEnum,
    MatchingModeEnum,
    OAuth2Provider,
    RedirectURI,
    SubModeEnum,
    ValidationError,
} from "@goauthentik/api";

import { propertyMappingsProvider, propertyMappingsSelector } from "./OAuth2ProviderFormHelpers.js";
import { oauth2ProvidersProvider, oauth2ProvidersSelector } from "./OAuth2ProvidersProvider.js";
import { oauth2SourcesProvider, oauth2SourcesSelector } from "./OAuth2Sources.js";

export const clientTypeOptions = [
    {
        label: msg("Confidential"),
        value: ClientTypeEnum.Confidential,
        default: true,
        description: html`${msg(
            "Confidential clients are capable of maintaining the confidentiality of their credentials such as client secrets",
        )}`,
    },
    {
        label: msg("Public"),
        value: ClientTypeEnum.Public,
        description: html`${msg(
            "Public clients are incapable of maintaining the confidentiality and should use methods like PKCE. ",
        )}`,
    },
];

export const subjectModeOptions = [
    {
        label: msg("Based on the User's hashed ID"),
        value: SubModeEnum.HashedUserId,
        default: true,
    },
    {
        label: msg("Based on the User's ID"),
        value: SubModeEnum.UserId,
    },
    {
        label: msg("Based on the User's UUID"),
        value: SubModeEnum.UserUuid,
    },
    {
        label: msg("Based on the User's username"),
        value: SubModeEnum.UserUsername,
    },
    {
        label: msg("Based on the User's Email"),
        value: SubModeEnum.UserEmail,
        description: html`${msg("This is recommended over the UPN mode.")}`,
    },
    {
        label: msg("Based on the User's UPN"),
        value: SubModeEnum.UserUpn,
        description: html`${msg(
            "Requires the user to have a 'upn' attribute set, and falls back to hashed user ID. Use this mode only if you have different UPN and Mail domains.",
        )}`,
    },
];

export const issuerModeOptions = [
    {
        label: msg("Each provider has a different issuer, based on the application slug"),
        value: IssuerModeEnum.PerProvider,
        default: true,
    },
    {
        label: msg("Same identifier is used for all providers"),
        value: IssuerModeEnum.Global,
    },
];

const redirectUriHelpMessages = [
    msg(
        "Valid redirect URIs after a successful authorization flow. Also specify any origins here for Implicit flows.",
    ),
    msg(
        "If no explicit redirect URIs are specified, the first successfully used redirect URI will be saved.",
    ),
    msg(
        'To allow any redirect URI, set the mode to Regex and the value to ".*". Be aware of the possible security implications this can have.',
    ),
];

export const redirectUriHelp = html`${redirectUriHelpMessages.map(
    (m) => html`<p class="pf-c-form__helper-text">${m}</p>`,
)}`;

type ShowClientSecret = (show: boolean) => void;
const defaultShowClientSecret: ShowClientSecret = (_show) => undefined;

export function renderForm(
    provider: Partial<OAuth2Provider>,
    errors: ValidationError,
    showClientSecret = false,
    showClientSecretCallback: ShowClientSecret = defaultShowClientSecret,
) {
    return html` <ak-text-input
            name="name"
            label=${msg("Name")}
            value=${ifDefined(provider?.name)}
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
        <ak-form-group expanded>
            <span slot="header"> ${msg("Protocol settings")} </span>
            <div slot="body" class="pf-c-form">
                <ak-radio-input
                    name="clientType"
                    label=${msg("Client type")}
                    .value=${provider?.clientType}
                    required
                    @change=${(ev: CustomEvent<{ value: ClientTypeEnum }>) => {
                        showClientSecretCallback(ev.detail.value !== ClientTypeEnum.Public);
                    }}
                    .options=${clientTypeOptions}
                >
                </ak-radio-input>
                <ak-text-input
                    name="clientId"
                    label=${msg("Client ID")}
                    value="${first(provider?.clientId, randomString(40, ascii_letters + digits))}"
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
                    ?hidden=${!showClientSecret}
                >
                </ak-text-input>
                <ak-form-element-horizontal
                    label=${msg("Redirect URIs/Origins (RegEx)")}
                    required
                    name="redirectUris"
                >
                    <ak-array-input
                        .items=${provider?.redirectUris ?? []}
                        .newItem=${() => ({ matchingMode: MatchingModeEnum.Strict, url: "" })}
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

                <ak-form-element-horizontal label=${msg("Signing Key")} name="signingKey">
                    <!-- NOTE: 'null' cast to 'undefined' on signingKey to satisfy Lit requirements -->
                    <ak-crypto-certificate-search
                        certificate=${ifDefined(provider?.signingKey ?? undefined)}
                        singleton
                    ></ak-crypto-certificate-search>
                    <p class="pf-c-form__helper-text">${msg("Key used to sign the tokens.")}</p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${msg("Encryption Key")} name="encryptionKey">
                    <!-- NOTE: 'null' cast to 'undefined' on encryptionKey to satisfy Lit requirements -->
                    <ak-crypto-certificate-search
                        certificate=${ifDefined(provider?.encryptionKey ?? undefined)}
                    ></ak-crypto-certificate-search>
                    <p class="pf-c-form__helper-text">${msg("Key used to encrypt the tokens.")}</p>
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
                    <ak-dual-select-dynamic-selected
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(provider?.propertyMappings)}
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
                    help=${msg("Configure how the issuer field of the ID Token should be filled.")}
                >
                </ak-radio-input>
            </div>
        </ak-form-group>

        <ak-form-group>
            <span slot="header">${msg("Machine-to-Machine authentication settings")}</span>
            <div slot="body" class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Federated OIDC Sources")}
                    name="jwtFederationSources"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${oauth2SourcesProvider}
                        .selector=${oauth2SourcesSelector(provider?.jwtFederationSources)}
                        available-label=${msg("Available Sources")}
                        selected-label=${msg("Selected Sources")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "JWTs signed by certificates configured in the selected sources can be used to authenticate to this provider.",
                        )}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Federated OIDC Providers")}
                    name="jwtFederationProviders"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${oauth2ProvidersProvider}
                        .selector=${oauth2ProvidersSelector(provider?.jwtFederationProviders)}
                        available-label=${msg("Available Providers")}
                        selected-label=${msg("Selected Providers")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "JWTs signed by the selected providers can be used to authenticate to this provider.",
                        )}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>`;
}
