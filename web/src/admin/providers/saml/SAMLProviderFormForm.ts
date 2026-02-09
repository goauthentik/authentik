import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";

import { propertyMappingsProvider, propertyMappingsSelector } from "./SAMLProviderFormHelpers.js";
import {
    availableHashes,
    digestAlgorithmOptions,
    retrieveSignatureAlgorithm,
    SAMLSupportedKeyTypes,
} from "./SAMLProviderOptions.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { RadioOption } from "#elements/forms/Radio";

import {
    FlowsInstancesListDesignationEnum,
    KeyTypeEnum,
    PropertymappingsApi,
    PropertymappingsProviderSamlListRequest,
    SAMLBindingsEnum,
    SAMLLogoutMethods,
    SAMLNameIDPolicyEnum,
    SAMLPropertyMapping,
    SAMLProvider,
    ValidationError,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const serviceProviderBindingOptions: RadioOption<SAMLBindingsEnum>[] = [
    {
        label: msg("Redirect"),
        value: SAMLBindingsEnum.Redirect,
    },
    {
        label: msg("Post"),
        value: SAMLBindingsEnum.Post,
    },
];

function renderHasSigningKp(provider: Partial<SAMLProvider>) {
    return html` <ak-switch-input
            name="signAssertion"
            label=${msg("Sign assertions")}
            ?checked=${provider.signAssertion ?? true}
            help=${msg("When enabled, the assertion element of the SAML response will be signed.")}
        >
        </ak-switch-input>

        <ak-switch-input
            name="signResponse"
            label=${msg("Sign responses")}
            ?checked=${provider.signResponse ?? false}
            help=${msg("When enabled, the SAML response will be signed.")}
        >
        </ak-switch-input>
        <ak-switch-input
            name="signLogoutRequest"
            label=${msg("Sign logout requests")}
            ?checked=${provider?.signLogoutRequest ?? false}
            help=${msg("When enabled, SAML logout requests will be signed.")}
        >
        </ak-switch-input>`;
}

function renderHasSlsUrl(
    provider: Partial<SAMLProvider>,
    hasPostBinding: boolean = false,
    setSlsBinding: (ev: Event) => void,
    logoutMethod: string,
    setLogoutMethod?: (ev: Event) => void,
) {
    const logoutMethodOptions: RadioOption<string>[] = [
        {
            label: msg("Front-channel (Iframe)"),
            value: SAMLLogoutMethods.FrontchannelIframe,
            default: true,
        },
        {
            label: msg("Front-channel (Native)"),
            value: SAMLLogoutMethods.FrontchannelNative,
        },
        {
            label: msg("Back-channel (POST)"),
            value: SAMLLogoutMethods.Backchannel,
            disabled: !hasPostBinding,
        },
    ];

    return html`<ak-radio-input
            label=${msg("SLS Binding")}
            name="slsBinding"
            .options=${serviceProviderBindingOptions}
            .value=${provider?.slsBinding ?? SAMLBindingsEnum.Redirect}
            help=${msg(
                "Determines how authentik sends the logout response back to the Service Provider.",
            )}
            @change=${setSlsBinding}
        >
        </ak-radio-input>
        <ak-radio-input
            label=${msg("Logout Method")}
            name="logoutMethod"
            .options=${logoutMethodOptions}
            .value=${logoutMethod}
            help=${msg("Method to use for logout when SLS URL is configured.")}
            @change=${setLogoutMethod}
        >
        </ak-radio-input>`;
}
export interface SAMLProviderFormProps {
    provider?: Partial<SAMLProvider>;
    errors?: ValidationError;
    setHasSigningKp: (ev: InputEvent) => void;
    hasSigningKp: boolean;
    signingKeyType: KeyTypeEnum | null;
    setHasSlsUrl: (ev: Event) => void;
    hasSlsUrl: boolean;
    setSlsBinding: (ev: Event) => void;
    hasPostBinding: boolean;
    logoutMethod: string;
    setLogoutMethod?: (ev: Event) => void;
}

export function renderForm({
    provider = {},
    errors = {},
    setHasSigningKp,
    hasSigningKp,
    signingKeyType,
    setHasSlsUrl,
    hasSlsUrl,
    setSlsBinding,
    hasPostBinding,
    logoutMethod,
    setLogoutMethod,
}: SAMLProviderFormProps) {
    // Get available hash algorithms for the selected key type
    const keyType = signingKeyType ?? KeyTypeEnum.Rsa;

    return html` <ak-text-input
            name="name"
            value=${ifDefined(provider.name)}
            label=${msg("Name")}
            required
            .errorMessages=${errors.name}
        ></ak-text-input>
        <ak-form-element-horizontal
            name="authorizationFlow"
            label=${msg("Authorization flow")}
            required
        >
            <ak-flow-search
                flowType=${FlowsInstancesListDesignationEnum.Authorization}
                .currentFlow=${provider.authorizationFlow}
                .errorMessages=${errors.authorizationFlow}
                required
            ></ak-flow-search>
            <p class="pf-c-form__helper-text">
                ${msg("Flow used when authorizing this provider.")}
            </p>
        </ak-form-element-horizontal>

        <ak-form-group open label="${msg("Protocol settings")}">
            <div class="pf-c-form">
                <ak-text-input
                    name="acsUrl"
                    label=${msg("ACS URL")}
                    placeholder=${msg("https://...")}
                    input-hint="code"
                    inputmode="url"
                    value="${ifDefined(provider.acsUrl)}"
                    required
                    .errorMessages=${errors.acsUrl}
                ></ak-text-input>
                <ak-text-input
                    label=${msg("Issuer")}
                    input-hint="code"
                    name="issuer"
                    value="${provider.issuer || "authentik"}"
                    required
                    .errorMessages=${errors.issuer}
                    help=${msg("Also known as Entity ID.")}
                ></ak-text-input>
                <ak-text-input
                    name="audience"
                    label=${msg("Audience")}
                    placeholder="https://..."
                    input-hint="code"
                    inputmode="url"
                    value="${ifDefined(provider.audience)}"
                    .errorMessages=${errors.audience}
                ></ak-text-input>
                <ak-text-input
                    name="slsUrl"
                    label=${msg("SLS URL")}
                    placeholder=${msg("https://...")}
                    input-hint="code"
                    inputmode="url"
                    value="${ifDefined(provider.slsUrl)}"
                    .errorMessages=${errors.slsUrl}
                    help=${msg(
                        "Optional Single Logout Service URL to send logout responses to. If not set, no logout response will be sent.",
                    )}
                    @input=${setHasSlsUrl}
                ></ak-text-input>
                ${hasSlsUrl
                    ? renderHasSlsUrl(
                          provider,
                          hasPostBinding,
                          setSlsBinding,
                          logoutMethod,
                          setLogoutMethod,
                      )
                    : nothing}
            </div>
        </ak-form-group>

        <ak-form-group label="${msg("Advanced flow settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Authentication flow")}
                    name="authenticationFlow"
                >
                    <ak-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authentication}
                        .currentFlow=${provider.authenticationFlow}
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
                        .currentFlow=${provider.invalidationFlow}
                        defaultFlowSlug="default-provider-invalidation-flow"
                        required
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used when logging out of this provider.")}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>

        <ak-form-group label="${msg("Advanced protocol settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal label=${msg("Signing Certificate")} name="signingKp">
                    <ak-crypto-certificate-search
                        .certificate=${provider.signingKp}
                        @input=${setHasSigningKp}
                        singleton
                        .allowedKeyTypes=${SAMLSupportedKeyTypes}
                    ></ak-crypto-certificate-search>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Certificate used to sign outgoing Responses going to the Service Provider.",
                        )}
                    </p>
                </ak-form-element-horizontal>
                ${hasSigningKp ? renderHasSigningKp(provider) : nothing}

                <ak-form-element-horizontal
                    label=${msg("Verification Certificate")}
                    name="verificationKp"
                >
                    <ak-crypto-certificate-search
                        .certificate=${provider.verificationKp}
                        nokey
                        .allowedKeyTypes=${SAMLSupportedKeyTypes}
                    ></ak-crypto-certificate-search>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "When selected, incoming assertion's Signatures will be validated against this certificate. To allow unsigned Requests, leave on default.",
                        )}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Encryption Certificate")}
                    name="encryptionKp"
                >
                    <ak-crypto-certificate-search
                        .certificate=${provider.encryptionKp}
                        nokey
                        .allowedKeyTypes=${SAMLSupportedKeyTypes}
                    ></ak-crypto-certificate-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("When selected, assertions will be encrypted using this keypair.")}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Property mappings")}
                    name="propertyMappings"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(provider.propertyMappings)}
                        available-label=${msg("Available User Property Mappings")}
                        selected-label=${msg("Selected User Property Mappings")}
                    ></ak-dual-select-dynamic-selected>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("NameID Property Mapping")}
                    name="nameIdMapping"
                >
                    <ak-search-select
                        .fetchObjects=${async (query?: string): Promise<SAMLPropertyMapping[]> => {
                            const args: PropertymappingsProviderSamlListRequest = {
                                ordering: "saml_name",
                            };
                            if (query !== undefined) {
                                args.search = query;
                            }
                            const items = await new PropertymappingsApi(
                                DEFAULT_CONFIG,
                            ).propertymappingsProviderSamlList(args);
                            return items.results;
                        }}
                        .renderElement=${(item: SAMLPropertyMapping): string => {
                            return item.name;
                        }}
                        .value=${(item: SAMLPropertyMapping | undefined): string | undefined => {
                            return item?.pk;
                        }}
                        .selected=${(item: SAMLPropertyMapping): boolean => {
                            return provider.nameIdMapping === item.pk;
                        }}
                        blankable
                    >
                    </ak-search-select>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Configure how the NameID value will be created. When left empty, the NameIDPolicy of the incoming request will be respected.",
                        )}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("AuthnContextClassRef Property Mapping")}
                    name="authnContextClassRefMapping"
                >
                    <ak-search-select
                        .fetchObjects=${async (query?: string): Promise<SAMLPropertyMapping[]> => {
                            const args: PropertymappingsProviderSamlListRequest = {
                                ordering: "saml_name",
                            };
                            if (query !== undefined) {
                                args.search = query;
                            }
                            const items = await new PropertymappingsApi(
                                DEFAULT_CONFIG,
                            ).propertymappingsProviderSamlList(args);
                            return items.results;
                        }}
                        .renderElement=${(item: SAMLPropertyMapping): string => {
                            return item.name;
                        }}
                        .value=${(item: SAMLPropertyMapping | undefined): string | undefined => {
                            return item?.pk;
                        }}
                        .selected=${(item: SAMLPropertyMapping): boolean => {
                            return provider.authnContextClassRefMapping === item.pk;
                        }}
                        blankable
                    >
                    </ak-search-select>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Configure how the AuthnContextClassRef value will be created. When left empty, the AuthnContextClassRef will be set based on which authentication methods the user used to authenticate.",
                        )}
                    </p>
                </ak-form-element-horizontal>

                <ak-text-input
                    name="assertionValidNotBefore"
                    label=${msg("Assertion valid not before")}
                    value="${provider.assertionValidNotBefore || "minutes=-5"}"
                    required
                    .errorMessages=${errors.assertionValidNotBefore}
                    help=${msg("Configure the maximum allowed time drift for an assertion.")}
                ></ak-text-input>

                <ak-text-input
                    name="assertionValidNotOnOrAfter"
                    label=${msg("Assertion valid not on or after")}
                    value="${provider.assertionValidNotOnOrAfter || "minutes=5"}"
                    required
                    .errorMessages=${errors.assertionValidNotBefore}
                    help=${msg("Assertion not valid on or after current time + this value.")}
                ></ak-text-input>

                <ak-text-input
                    name="sessionValidNotOnOrAfter"
                    label=${msg("Session valid not on or after")}
                    value="${provider.sessionValidNotOnOrAfter || "minutes=86400"}"
                    required
                    .errorMessages=${errors.sessionValidNotOnOrAfter}
                    help=${msg("Session not valid on or after current time + this value.")}
                ></ak-text-input>

                <ak-text-input
                    name="defaultRelayState"
                    label=${msg("Default relay state")}
                    value="${provider.defaultRelayState || ""}"
                    .errorMessages=${errors.sessionValidNotOnOrAfter}
                    help=${msg(
                        "When using IDP-initiated logins, the relay state will be set to this value.",
                    )}
                ></ak-text-input>
                <ak-radio-input
                    label=${msg("Service Provider Binding")}
                    name="spBinding"
                    .options=${serviceProviderBindingOptions}
                    .value=${provider.spBinding ?? SAMLBindingsEnum.Post}
                    help=${msg(
                        "Determines how authentik sends the response back to the Service Provider.",
                    )}
                ></ak-radio-input>
                <ak-form-element-horizontal
                    label=${msg("Default NameID Policy")}
                    required
                    name="defaultNameIdPolicy"
                >
                    <select class="pf-c-form-control">
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent}
                            ?selected=${provider?.defaultNameIdPolicy ===
                            SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent}
                        >
                            ${msg("Persistent")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                            ?selected=${provider?.defaultNameIdPolicy ===
                            SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                        >
                            ${msg("Email address")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                            ?selected=${provider?.defaultNameIdPolicy ===
                            SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                        >
                            ${msg("Windows")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                            ?selected=${provider?.defaultNameIdPolicy ===
                            SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                        >
                            ${msg("X509 Subject")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                            ?selected=${provider?.defaultNameIdPolicy ===
                            SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                        >
                            ${msg("Transient")}
                        </option>
                    </select>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Configure the default NameID Policy used by IDP-initiated logins and when an incoming assertion doesn't specify a NameID Policy (also applies when using a custom NameID Mapping).",
                        )}
                    </p>
                </ak-form-element-horizontal>

                <ak-form-element-horizontal
                    label=${msg("Digest algorithm")}
                    required
                    name="digestAlgorithm"
                >
                    <select class="pf-c-form-control">
                        ${digestAlgorithmOptions.map(
                            (opt) => html`
                                <option
                                    value=${opt.value}
                                    ?selected=${provider?.digestAlgorithm === opt.value ||
                                    (!provider?.digestAlgorithm && opt.default)}
                                >
                                    ${opt.label}
                                </option>
                            `,
                        )}
                    </select>
                </ak-form-element-horizontal>

                <ak-form-element-horizontal
                    label=${msg("Signature algorithm")}
                    required
                    name="signatureAlgorithm"
                >
                    <select class="pf-c-form-control">
                        ${availableHashes.map((hash) => {
                            const algorithmValue = retrieveSignatureAlgorithm(keyType, hash);
                            if (!algorithmValue) return nothing;

                            // Default to sha256 or selected sha algorithm if valid
                            // when switching selected certs
                            const isCurrentAlgorithmAvailable = availableHashes.some(
                                (h) =>
                                    retrieveSignatureAlgorithm(keyType, h) ===
                                    provider?.signatureAlgorithm,
                            );

                            return html`
                                <option
                                    value=${algorithmValue}
                                    ?selected=${provider?.signatureAlgorithm === algorithmValue ||
                                    (!isCurrentAlgorithmAvailable && hash === "SHA256")}
                                >
                                    ${hash}
                                </option>
                            `;
                        })}
                    </select>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>`;
}
