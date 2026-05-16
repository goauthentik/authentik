import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/ak-search-select-ez";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { withQuery } from "#elements/forms/SearchSelect/utils";

import { AKLabel } from "#components/ak-label";

import {
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "#admin/providers/saml/SAMLProviderFormHelpers";
import {
    availableHashes,
    DEFAULT_HASH_ALGORITHM,
    digestAlgorithmOptions,
    retrieveSignatureAlgorithm,
    SAMLSupportedKeyTypes,
} from "#admin/providers/saml/SAMLProviderOptions";

import {
    FlowDesignationEnum,
    KeyTypeEnum,
    PropertymappingsApi,
    SAMLNameIDPolicyEnum,
    SAMLPropertyMapping,
    ValidationError,
    WSFederationProvider,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

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
    setHasSigningKp: (ev: InputEvent) => void;
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
    const samlPropertyMappingSearch = async (query?: string) =>
        (
            await new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderSamlList(
                withQuery(query, { ordering: "saml_name" }),
            )
        ).results;

    const nameIdMappingConfig = {
        fetchObjects: samlPropertyMappingSearch,
        renderElement: (item: SAMLPropertyMapping) => item.name,
        value: (item: SAMLPropertyMapping | undefined) => item?.pk,
        selected: (item: SAMLPropertyMapping) => provider.nameIdMapping === item.pk,
    };

    const authnContextClassRefMappingConfig = {
        fetchObjects: samlPropertyMappingSearch,
        renderElement: (item: SAMLPropertyMapping) => item.name,
        value: (item: SAMLPropertyMapping | undefined) => item?.pk,
        selected: (item: SAMLPropertyMapping) => provider.authnContextClassRefMapping === item.pk,
    };

    return html` <ak-text-input
            name="name"
            label=${msg("Provider Name")}
            placeholder=${msg("Type a provider name...")}
            spellcheck="false"
            value=${ifDefined(provider.name)}
            required
            .errorMessages=${errors.name}
        ></ak-text-input>
        <ak-form-element-horizontal name="authorizationFlow" required>
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                    htmlFor: "authorizationFlow",
                    required: true,
                },
                msg("Authorization Flow"),
            )}
            <ak-flow-search
                id="authorizationFlow"
                flowType=${FlowDesignationEnum.Authorization}
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
                <ak-form-element-horizontal name="authenticationFlow">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "authenticationFlow",
                        },
                        msg("Authentication Flow"),
                    )}
                    <ak-flow-search
                        id="authenticationFlow"
                        flowType=${FlowDesignationEnum.Authentication}
                        .currentFlow=${provider.authenticationFlow}
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Flow used when a user access this provider and is not authenticated.",
                        )}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="invalidationFlow" required>
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "invalidationFlow",
                            required: true,
                        },
                        msg("Invalidation Flow"),
                    )}
                    <ak-flow-search
                        id="invalidationFlow"
                        flowType=${FlowDesignationEnum.Invalidation}
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
                <ak-form-element-horizontal name="signingKp">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "signingKp",
                        },
                        msg("Signing Certificate"),
                    )}
                    <ak-crypto-certificate-search
                        id="signingKp"
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
                ${hasSigningKp
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
                    : nothing}

                <ak-form-element-horizontal name="encryptionKp">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "encryptionKp",
                        },
                        msg("Encryption Certificate"),
                    )}
                    <ak-crypto-certificate-search
                        id="encryptionKp"
                        .certificate=${provider.encryptionKp}
                        nokey
                        .allowedKeyTypes=${SAMLSupportedKeyTypes}
                    ></ak-crypto-certificate-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("When selected, assertions will be encrypted using this keypair.")}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="propertyMappings">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "propertyMappings",
                        },
                        msg("Property mappings"),
                    )}
                    <ak-dual-select-dynamic-selected
                        id="propertyMappings"
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(provider.propertyMappings)}
                        available-label=${msg("Available User Property Mappings")}
                        selected-label=${msg("Selected User Property Mappings")}
                    ></ak-dual-select-dynamic-selected>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="nameIdMapping">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "nameIdMapping",
                        },
                        msg("NameID Property Mapping"),
                    )}
                    <ak-search-select-ez
                        id="nameIdMapping"
                        .config=${nameIdMappingConfig}
                        blankable
                    ></ak-search-select-ez>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Configure how the NameID value will be created. When left empty, the NameIDPolicy of the incoming request will be respected.",
                        )}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="authnContextClassRefMapping">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "authnContextClassRefMapping",
                        },
                        msg("AuthnContextClassRef Property Mapping"),
                    )}
                    <ak-search-select-ez
                        id="authnContextClassRefMapping"
                        .config=${authnContextClassRefMappingConfig}
                        blankable
                    ></ak-search-select-ez>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Configure how the AuthnContextClassRef value will be created. When left empty, the AuthnContextClassRef will be set based on which authentication methods the user used to authenticate.",
                        )}
                    </p>
                </ak-form-element-horizontal>

                <ak-text-input
                    name="sessionValidNotOnOrAfter"
                    label=${msg("Session valid not on or after")}
                    value="${provider.sessionValidNotOnOrAfter || "minutes=86400"}"
                    required
                    .errorMessages=${errors.sessionValidNotOnOrAfter}
                    help=${msg("Session not valid on or after current time + this value.")}
                ></ak-text-input>
                <ak-form-element-horizontal required name="defaultNameIdPolicy">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "defaultNameIdPolicy",
                            required: true,
                        },
                        msg("Default NameID Policy"),
                    )}
                    <select id="defaultNameIdPolicy" class="pf-c-form-control">
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

                <ak-form-element-horizontal required name="digestAlgorithm">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "digestAlgorithm",
                            required: true,
                        },
                        msg("Digest algorithm"),
                    )}
                    <select id="digestAlgorithm" class="pf-c-form-control">
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

                <ak-form-element-horizontal required name="signatureAlgorithm">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "signatureAlgorithm",
                            required: true,
                        },
                        msg("Signature algorithm"),
                    )}
                    <select id="signatureAlgorithm" class="pf-c-form-control">
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
                                    ?selected=${provider?.signatureAlgorithm === algorithmValue ||
                                    (!isCurrentAlgorithmAvailable &&
                                        hash === DEFAULT_HASH_ALGORITHM)}
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
