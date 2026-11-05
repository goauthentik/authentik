import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#elements/ak-array-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#admin/providers/saml/SAMLProviderACSURL";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";
import { propertyMappingsProvider, propertyMappingsSelector } from "./SAMLProviderFormHelpers.js";
import {
    availableHashes,
    DEFAULT_HASH_ALGORITHM,
    digestAlgorithmOptions,
    encryptionAlgorithmOptions,
    logoutMethodOptions,
    retrieveSignatureAlgorithm,
} from "./SAMLProviderOptions.js";

import { RadioOption } from "#elements/forms/Radio";
import type { SearchSelectChangeEvent } from "#elements/forms/SearchSelect/events";

import { AKCertificateSearch } from "#admin/common/AKCertificateSearch";
import { XMLSigningKeyTypes } from "#admin/common/certificate-key-types";
import {
    AKAuthenticationFlowField,
    AKAuthorizationFlowField,
    AKInvalidationFlowField,
} from "#admin/providers/components/flow-fields";
import {
    AKAuthnContextClassRefMappingField,
    AKNameIDMappingField,
} from "#admin/providers/components/saml-property-mapping-fields";
import {
    oauth2ProvidersProvider,
    oauth2ProvidersSelector,
} from "#admin/providers/oauth2/OAuth2ProvidersProvider";

import {
    KeyTypeEnum,
    MatchingModeEnum,
    SAMLACSURL,
    SAMLBindingsEnum,
    SAMLNameIDPolicyEnum,
    SAMLProvider,
    ValidationError,
    CertificateKeyPair,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { guard } from "lit/directives/guard.js";
import { ifDefined } from "lit/directives/if-defined.js";

const acsURLHelpMessages: string[] = [
    msg(
        "URLs the Service Provider may receive responses at. A request's ACS URL or index must match one of these.",
        { id: "provider.saml.acs-urls.description" },
    ),
    msg(
        "The default URL is used for IdP-initiated logins and for requests that don't specify an ACS URL. Without an explicit default, the first strict URL is used.",
        { id: "provider.saml.acs-urls.default.description" },
    ),
    msg(
        "Regex URLs must match the entire requested URL. Be aware of the security implications, as responses are sent to any URL the expression matches.",
        { id: "provider.saml.acs-urls.regex.description" },
    ),
];

/**
 * ACS URLs to show for `provider`, starting new providers with a single empty default entry.
 */
function initialACSURLs(provider: Partial<SAMLProvider>): SAMLACSURL[] {
    if (provider.acsUrls?.length) return provider.acsUrls;

    return [
        {
            matchingMode: MatchingModeEnum.Strict,
            url: provider.acsUrl ?? "",
            index: null,
            isDefault: true,
        },
    ];
}

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
        </ak-switch-input>
        <ak-switch-input
            name="signLogoutResponse"
            label=${msg("Sign logout response")}
            ?checked=${provider?.signLogoutResponse ?? false}
            help=${msg("When enabled, SAML logout responses will be signed.")}
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
            .options=${logoutMethodOptions(hasPostBinding)}
            .value=${logoutMethod}
            help=${msg("Method to use for logout when SLS URL is configured.")}
            @change=${setLogoutMethod}
        >
        </ak-radio-input>`;
}

export interface SAMLProviderFormProps {
    provider?: Partial<SAMLProvider> | null;
    errors?: ValidationError | null;
    setHasSigningKp: (event: SearchSelectChangeEvent<CertificateKeyPair>) => void;
    hasSigningKp: boolean;
    signingKeyType: KeyTypeEnum | null;
    setHasEncryptionKp: (event: SearchSelectChangeEvent<CertificateKeyPair>) => void;
    hasEncryptionKp: boolean;
    setHasSlsUrl: (ev: Event) => void;
    hasSlsUrl: boolean;
    setSlsBinding: (ev: Event) => void;
    hasPostBinding: boolean;
    logoutMethod: string;
    setLogoutMethod?: (ev: Event) => void;
}

export function renderForm({
    provider,
    errors,
    setHasSigningKp,
    hasSigningKp,
    signingKeyType,
    setHasEncryptionKp,
    hasEncryptionKp,
    setHasSlsUrl,
    hasSlsUrl,
    setSlsBinding,
    hasPostBinding,
    logoutMethod,
    setLogoutMethod,
}: SAMLProviderFormProps) {
    provider ||= {};
    errors ||= {};

    // Get available hash algorithms for the selected key type
    const keyType = signingKeyType ?? KeyTypeEnum.Rsa;

    return html` <ak-text-input
            name="name"
            value=${ifDefined(provider.name)}
            label=${msg("Name")}
            required
            .errorMessages=${errors.name}
        ></ak-text-input>
        ${AKAuthorizationFlowField({
            value: provider.authorizationFlow,
            errors: errors.authorizationFlow,
        })}

        <ak-form-group open label="${msg("Protocol settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("ACS URLs", { id: "provider.saml.acs-urls.label" })}
                    name="acsUrls"
                    required
                    .errorMessages=${errors.acsUrls}
                >
                    <ak-array-input
                        required
                        .items=${guard([provider.acsUrls, provider.acsUrl], () =>
                            initialACSURLs(provider),
                        )}
                        .newItem=${(): SAMLACSURL => ({
                            matchingMode: MatchingModeEnum.Strict,
                            url: "",
                            index: null,
                            isDefault: false,
                        })}
                        .row=${(acsURL: SAMLACSURL, idx: number) => {
                            return html`<ak-provider-saml-acs-url
                                .acsURL=${acsURL}
                                name="saml-acs-url"
                                style="width: 100%"
                                input-id="acs-url-${idx}"
                            ></ak-provider-saml-acs-url>`;
                        }}
                    >
                    </ak-array-input>
                    ${acsURLHelpMessages.map(
                        (m) => html`<p class="pf-c-form__helper-text">${m}</p>`,
                    )}
                </ak-form-element-horizontal>
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
                ${
                    hasSlsUrl
                        ? renderHasSlsUrl(
                              provider,
                              hasPostBinding,
                              setSlsBinding,
                              logoutMethod,
                              setLogoutMethod,
                          )
                        : nothing
                }
            </div>
        </ak-form-group>

        <ak-form-group label="${msg("Advanced flow settings")}">
            <div class="pf-c-form">
                ${AKAuthenticationFlowField({ value: provider.authenticationFlow })}
                ${AKInvalidationFlowField({ value: provider.invalidationFlow })}
            </div>
        </ak-form-group>

        <ak-form-group label="${msg("Advanced protocol settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal label=${msg("Signing Certificate")} name="signingKp">
                    ${AKCertificateSearch({ name: "signingKp", value: provider.signingKp, singleton: true, allowedKeyTypes: XMLSigningKeyTypes, onChange: setHasSigningKp })}
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
                    ${AKCertificateSearch({ name: "verificationKp", value: provider.verificationKp, noKey: true, allowedKeyTypes: XMLSigningKeyTypes })}
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
                    ${AKCertificateSearch({ name: "encryptionKp", value: provider.encryptionKp, noKey: true, allowedKeyTypes: XMLSigningKeyTypes, onChange: setHasEncryptionKp })}
                    <p class="pf-c-form__helper-text">
                        ${msg("When selected, assertions will be encrypted using this keypair.")}
                    </p>
                </ak-form-element-horizontal>
                ${
                    hasEncryptionKp
                        ? html`<ak-form-element-horizontal
                              label=${msg("Encryption algorithm")}
                              required
                              name="encryptionAlgorithm"
                          >
                              <select class="pf-c-form-control">
                                  ${encryptionAlgorithmOptions.map(
                                      (opt) => html`
                                          <option
                                              value=${opt.value}
                                              ?selected=${
                                                  provider?.encryptionAlgorithm === opt.value ||
                                                  (!provider?.encryptionAlgorithm && opt.default)
                                              }
                                          >
                                              ${opt.label}
                                          </option>
                                      `,
                                  )}
                              </select>
                              <p class="pf-c-form__helper-text">
                                  ${msg("Block cipher used to encrypt the assertion.")}
                              </p>
                          </ak-form-element-horizontal>`
                        : nothing
                }
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
                ${AKNameIDMappingField({ value: provider.nameIdMapping })}
                ${AKAuthnContextClassRefMappingField({ value: provider.authnContextClassRefMapping })}

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
                <ak-text-input
                    label=${msg("EntityID/Issuer override")}
                    name="issuerOverride"
                    value="${ifDefined(provider.issuerOverride ?? undefined)}"
                    .errorMessages=${errors.issuerOverride}
                    help=${msg(
                        "Sets a custom EntityID/Issuer to override the authentik generated default.",
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
                            ?selected=${
                                provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent
                            }
                        >
                            ${msg("Persistent")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                            ?selected=${
                                provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress
                            }
                        >
                            ${msg("Email address")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                            ?selected=${
                                provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName
                            }
                        >
                            ${msg("Windows")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                            ?selected=${
                                provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName
                            }
                        >
                            ${msg("X509 Subject")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                            ?selected=${
                                provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient
                            }
                        >
                            ${msg("Transient")}
                        </option>
                        <option
                            value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatUnspecified}
                            ?selected=${
                                provider?.defaultNameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatUnspecified
                            }
                        >
                            ${msg("Unspecified")}
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
                                    ?selected=${
                                        provider?.digestAlgorithm === opt.value ||
                                        (!provider?.digestAlgorithm && opt.default)
                                    }
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
                                    ?selected=${
                                        provider?.signatureAlgorithm === algorithmValue ||
                                        (!isCurrentAlgorithmAvailable &&
                                            hash === DEFAULT_HASH_ALGORITHM)
                                    }
                                >
                                    ${hash}
                                </option>
                            `;
                        })}
                    </select>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>

        <ak-form-group label="${msg("Machine-to-Machine authentication settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Federated OAuth2/OpenID Providers")}
                    name="jwtFederationProviders"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${oauth2ProvidersProvider}
                        .selector=${oauth2ProvidersSelector(provider.jwtFederationProviders)}
                        available-label=${msg("Available Providers")}
                        selected-label=${msg("Selected Providers")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Selected providers can exchange their JWTs for a SAML Response of this provider via token exchange.",
                        )}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>`;
}
