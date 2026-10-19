import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
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
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "#admin/providers/saml/SAMLProviderFormHelpers";
import {
    availableHashes,
    DEFAULT_HASH_ALGORITHM,
    digestAlgorithmOptions,
    retrieveSignatureAlgorithm,
} from "#admin/providers/saml/SAMLProviderOptions";

import {
    KeyTypeEnum,
    SAMLNameIDPolicyEnum,
    ValidationError,
    WSFederationProvider,
    WSFedSAMLVersionEnum,
    CertificateKeyPair,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

const samlVersionAndLabel = [
    [
        WSFedSAMLVersionEnum._11,
        msg("SAML 1.1 (required by Microsoft Entra ID / ADFS)", {
            id: "wsfed.saml-version.option.saml11",
        }),
    ],
    [WSFedSAMLVersionEnum._20, msg("SAML 2.0", { id: "wsfed.saml-version.option.saml20" })],
];

const samlNameIDPolicyAndLabel = [
    [SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent, msg("Persistent")],
    [SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress, msg("Email address")],
    [
        SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName,
        msg("Windows"),
    ],
    [SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName, msg("X509 Subject")],
    [SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient, msg("Transient")],
];

export interface WSFederationProviderFormProps {
    provider?: Partial<WSFederationProvider>;
    errors?: ValidationError;
    setHasSigningKp: (event: SearchSelectChangeEvent<CertificateKeyPair>) => void;
    hasSigningKp: boolean;
    signingKeyType: KeyTypeEnum | null;
}

export function renderForm({
    provider = {},
    errors = {},
    setHasSigningKp,
    hasSigningKp,
    signingKeyType,
}: WSFederationProviderFormProps) {
    const keyType = signingKeyType ?? KeyTypeEnum.Rsa;

    return html` <ak-text-input
            name="name"
            label=${msg("Provider Name")}
            placeholder=${msg("Type a provider name...")}
            spellcheck="false"
            value=${ifDefined(provider.name)}
            required
            .errorMessages=${errors.name}
        ></ak-text-input>
        ${AKAuthorizationFlowField({
            value: provider.authorizationFlow,
            errors: errors.authorizationFlow,
        })}

        <ak-form-group open label="${msg("Protocol settings")}">
            <div class="pf-c-form">
                <ak-text-input
                    name="replyUrl"
                    label=${msg("Reply URL")}
                    placeholder=${msg("https://...")}
                    input-hint="code"
                    inputmode="url"
                    value="${ifDefined(provider.replyUrl)}"
                    required
                    .errorMessages=${errors.replyUrl}
                ></ak-text-input>
                <ak-text-input
                    name="wtrealm"
                    label=${msg("Realm")}
                    input-hint="code"
                    value="${ifDefined(provider.wtrealm)}"
                    required
                    .errorMessages=${errors.wtrealm}
                ></ak-text-input>
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
                ${
                    hasSigningKp
                        ? html`<ak-switch-input
                                  name="signAssertion"
                                  label=${msg("Sign assertions")}
                                  ?checked=${provider.signAssertion ?? true}
                                  help=${msg(
                                      "When enabled, the assertion element of the SAML response will be signed.",
                                  )}
                              >
                              </ak-switch-input>
                              <ak-switch-input
                                  name="signLogoutRequest"
                                  label=${msg("Sign logout requests")}
                                  ?checked=${provider.signLogoutRequest ?? false}
                                  help=${msg("When enabled, SAML logout requests will be signed.")}
                              >
                              </ak-switch-input>`
                        : nothing
                }

                <ak-form-element-horizontal
                    label=${msg("Encryption Certificate")}
                    name="encryptionKp"
                >
                    ${AKCertificateSearch({ name: "encryptionKp", value: provider.encryptionKp, noKey: true, allowedKeyTypes: XMLSigningKeyTypes })}
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
                ${AKNameIDMappingField({ value: provider.nameIdMapping })}
                ${AKAuthnContextClassRefMappingField({ value: provider.authnContextClassRefMapping })}

                <ak-text-input
                    name="sessionValidNotOnOrAfter"
                    label=${msg("Session valid not on or after")}
                    value="${provider.sessionValidNotOnOrAfter || "minutes=86400"}"
                    required
                    .errorMessages=${errors.sessionValidNotOnOrAfter}
                    help=${msg("Session not valid on or after current time + this value.")}
                ></ak-text-input>
                <ak-form-element-horizontal
                    label=${msg("Default NameID Policy")}
                    required
                    name="defaultNameIdPolicy"
                >
                    <select class="pf-c-form-control">
                        ${samlNameIDPolicyAndLabel.map(
                            ([policy, label]) =>
                                html`<option
                                    value=${policy}
                                    ?selected=${provider?.defaultNameIdPolicy === policy}
                                >
                                    ${label}
                                </option>`,
                        )}
                    </select>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Configure the default NameID Policy used by IDP-initiated logins and when an incoming assertion doesn't specify a NameID Policy (also applies when using a custom NameID Mapping).",
                        )}
                    </p>
                </ak-form-element-horizontal>

                <ak-form-element-horizontal
                    label=${msg("SAML assertion version", {
                        id: "wsfed.saml-version.label",
                    })}
                    required
                    name="samlVersion"
                >
                    <select class="pf-c-form-control">
                        ${samlVersionAndLabel.map(
                            ([version, label]) => html`
                                <option
                                    value=${version}
                                    ?selected=${provider?.samlVersion === version}
                                >
                                    ${label}
                                </option>
                            `,
                        )}
                    </select>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Microsoft Entra ID and classic ADFS-style relying parties typically require SAML 1.1.",
                            { id: "wsfed.saml-version.description" },
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
        </ak-form-group>`;
}
