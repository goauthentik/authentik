import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-source-flow-search";
import "#components/ak-file-search-input";
import "#components/ak-slug-input";
import "#components/ak-text-input";
import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/utils/TimeDeltaHelp";

import { propertyMappingsProvider, propertyMappingsSelector } from "./SAMLSourceFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKLabel } from "#components/ak-label";

import { type AkCryptoCertificateSearch } from "#admin/common/ak-crypto-certificate-search";
import { iconHelperText, placeholderHelperText } from "#admin/helperText";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { BaseSourceForm } from "#admin/sources/BaseSourceForm";
import { GroupMatchingModeToLabel, UserMatchingModeToLabel } from "#admin/sources/oauth/utils";

import {
    BindingTypeEnum,
    DigestAlgorithmEnum,
    FlowDesignationEnum,
    GroupMatchingModeEnum,
    SAMLNameIDPolicyEnum,
    SAMLSource,
    SignatureAlgorithmEnum,
    SourcesApi,
    UsageEnum,
    UserMatchingModeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-source-saml-form")
export class SAMLSourceForm extends BaseSourceForm<SAMLSource> {
    @state()
    protected hasSigningCert = false;

    public override reset(): void {
        super.reset();

        this.hasSigningCert = false;
    }

    setHasSigningCert(ev: InputEvent): void {
        const target = ev.target as AkCryptoCertificateSearch;
        if (!target) return;
        this.hasSigningCert = !!target.selectedKeypair;
    }

    async loadInstance(pk: string): Promise<SAMLSource> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesSamlRetrieve({
            slug: pk,
        });
    }

    async send(data: SAMLSource): Promise<SAMLSource> {
        if (this.instance) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesSamlUpdate({
                slug: this.instance.slug,
                sAMLSourceRequest: data,
            });
        }

        return new SourcesApi(DEFAULT_CONFIG).sourcesSamlCreate({
            sAMLSourceRequest: data,
        });
    }

    renderHasSigningCert(): TemplateResult {
        return html`<ak-switch-input
                name="signedAssertion"
                label=${msg("Verify Assertion Signature")}
                ?checked=${this.instance?.signedAssertion ?? true}
                help=${msg(
                    "When enabled, authentik will look for a Signature inside of the Assertion element.",
                )}
            ></ak-switch-input>
            <ak-switch-input
                name="signedResponse"
                label=${msg("Verify Response Signature")}
                ?checked=${this.instance?.signedResponse ?? false}
                help=${msg(
                    "When enabled, authentik will look for a Signature inside of the Response element.",
                )}
            ></ak-switch-input>`;
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                label=${msg("Source Name")}
                placeholder=${msg("Type a name for this source...")}
                required
                name="name"
                value="${ifDefined(this.instance?.name)}"
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                placeholder=${msg("e.g. my-saml-source")}
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                input-hint="code"
            ></ak-slug-input>
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            ></ak-switch-input>
            <ak-switch-input
                name="promoted"
                label=${msg("Promoted")}
                ?checked=${this.instance?.promoted ?? false}
                help=${msg(
                    "When enabled, this source will be displayed as a prominent button on the login page, instead of a small icon.",
                )}
            ></ak-switch-input>
            <ak-form-element-horizontal required name="userMatchingMode">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "userMatchingMode",
                        required: true,
                    },
                    msg("User matching mode"),
                )}
                <select id="userMatchingMode" class="pf-c-form-control">
                    <option
                        value=${UserMatchingModeEnum.Identifier}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.Identifier}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailDeny)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameDeny)}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal required name="groupMatchingMode">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "groupMatchingMode",
                        required: true,
                    },
                    msg("Group matching mode"),
                )}
                <select id="groupMatchingMode" class="pf-c-form-control">
                    <option
                        value=${GroupMatchingModeEnum.Identifier}
                        ?selected=${this.instance?.groupMatchingMode ===
                        GroupMatchingModeEnum.Identifier}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                    </option>
                    <option
                        value=${GroupMatchingModeEnum.NameLink}
                        ?selected=${this.instance?.groupMatchingMode ===
                        GroupMatchingModeEnum.NameLink}
                    >
                        ${GroupMatchingModeToLabel(GroupMatchingModeEnum.NameLink)}
                    </option>
                    <option
                        value=${GroupMatchingModeEnum.NameDeny}
                        ?selected=${this.instance?.groupMatchingMode ===
                        GroupMatchingModeEnum.NameDeny}
                    >
                        ${GroupMatchingModeToLabel(GroupMatchingModeEnum.NameDeny)}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-file-search-input
                name="icon"
                label=${msg("Icon")}
                .value=${this.instance?.icon}
                .usage=${UsageEnum.Media}
                blankable
                help=${iconHelperText}
            ></ak-file-search-input>

            <ak-form-group open label="${msg("Protocol settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="ssoUrl">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "ssoUrl",
                                required: true,
                            },
                            msg("SSO URL"),
                        )}
                        <input
                            id="ssoUrl"
                            type="text"
                            value="${ifDefined(this.instance?.ssoUrl)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("URL that the initial Login request is sent to.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="sloUrl">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "sloUrl",
                            },
                            msg("SLO URL"),
                        )}
                        <input
                            id="sloUrl"
                            type="text"
                            value="${ifDefined(this.instance?.sloUrl || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Optional URL if the IDP supports Single-Logout.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="issuer">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "issuer",
                            },
                            msg("Issuer"),
                        )}
                        <input
                            id="issuer"
                            type="text"
                            value="${ifDefined(this.instance?.issuer)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Also known as Entity ID. Defaults the Metadata URL.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="bindingType">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "bindingType",
                                required: true,
                            },
                            msg("Binding Type"),
                        )}
                        <ak-radio
                            id="bindingType"
                            .options=${[
                                {
                                    label: msg("Redirect binding"),
                                    value: BindingTypeEnum.Redirect,
                                    default: true,
                                },
                                {
                                    label: msg("Post-auto binding"),
                                    value: BindingTypeEnum.PostAuto,
                                    description: html`${msg(
                                        "Post binding but the request is automatically sent and the user doesn't have to confirm.",
                                    )}`,
                                },
                                {
                                    label: msg("Post binding"),
                                    value: BindingTypeEnum.Post,
                                },
                            ]}
                            .value=${this.instance?.bindingType}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="signingKp">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "signingKp",
                            },
                            msg("Signing keypair"),
                        )}
                        <ak-crypto-certificate-search
                            id="signingKp"
                            .certificate=${this.instance?.signingKp}
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Keypair which is used to sign outgoing requests. Leave empty to disable signing.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="verificationKp">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "verificationKp",
                            },
                            msg("Verification Certificate"),
                        )}
                        <ak-crypto-certificate-search
                            id="verificationKp"
                            .certificate=${this.instance?.verificationKp}
                            @input=${this.setHasSigningCert}
                            nokey
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When selected, incoming assertion's Signatures will be validated against this certificate. To allow unsigned Requests, leave on default.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    ${this.hasSigningCert ? this.renderHasSigningCert() : nothing}
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Advanced protocol settings")}">
                <div class="pf-c-form">
                    <ak-switch-input
                        name="allowIdpInitiated"
                        label=${msg(" Allow IDP-initiated logins")}
                        ?checked=${this.instance?.allowIdpInitiated ?? false}
                        help=${msg(
                            "Allows authentication flows initiated by the IdP. This can be a security risk, as no validation of the request ID is done.",
                        )}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="forceAuthn"
                        label=${msg("Force authentication")}
                        ?checked=${!!this.instance?.forceAuthn}
                        help=${msg(
                            "When enabled, the IdP is requested to force re-authentication of the user, even if the user has an existing session.",
                        )}
                    ></ak-switch-input>
                    <ak-form-element-horizontal required name="nameIdPolicy">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "nameIdPolicy",
                                required: true,
                            },
                            msg("NameID Policy"),
                        )}
                        <select id="nameIdPolicy" class="pf-c-form-control">
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent}
                                ?selected=${this.instance?.nameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent}
                            >
                                ${msg("Persistent")}
                            </option>
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                                ?selected=${this.instance?.nameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                            >
                                ${msg("Email address")}
                            </option>
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                                ?selected=${this.instance?.nameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                            >
                                ${msg("Windows")}
                            </option>
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                                ?selected=${this.instance?.nameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                            >
                                ${msg("X509 Subject")}
                            </option>
                            <option
                                value=${SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                                ?selected=${this.instance?.nameIdPolicy ===
                                SAMLNameIDPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                            >
                                ${msg("Transient")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="userPathTemplate">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "userPathTemplate",
                            },
                            msg("User path"),
                        )}
                        <input
                            id="userPathTemplate"
                            type="text"
                            value="${this.instance?.userPathTemplate ??
                            "goauthentik.io/sources/%(slug)s"}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">${placeholderHelperText}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="temporaryUserDeleteAfter">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "temporaryUserDeleteAfter",
                                required: true,
                            },
                            msg("Delete temporary users after"),
                        )}
                        <input
                            id="temporaryUserDeleteAfter"
                            type="text"
                            value="${this.instance?.temporaryUserDeleteAfter || "days=1"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Time offset when temporary users should be deleted. This only applies if your IDP uses the NameID Format 'transient', and the user doesn't log out manually.",
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
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
                        <ak-radio
                            id="digestAlgorithm"
                            .options=${[
                                {
                                    label: "SHA1",
                                    value: DigestAlgorithmEnum.HttpWwwW3Org200009Xmldsigsha1,
                                },
                                {
                                    label: "SHA256",
                                    value: DigestAlgorithmEnum.HttpWwwW3Org200104Xmlencsha256,
                                    default: true,
                                },
                                {
                                    label: "SHA384",
                                    value: DigestAlgorithmEnum.HttpWwwW3Org200104XmldsigMoresha384,
                                },
                                {
                                    label: "SHA512",
                                    value: DigestAlgorithmEnum.HttpWwwW3Org200104Xmlencsha512,
                                },
                            ]}
                            .value=${this.instance?.digestAlgorithm}
                        >
                        </ak-radio>
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
                        <ak-radio
                            id="signatureAlgorithm"
                            .options=${[
                                {
                                    label: "RSA-SHA1",
                                    value: SignatureAlgorithmEnum.HttpWwwW3Org200009XmldsigrsaSha1,
                                },
                                {
                                    label: "RSA-SHA256",
                                    value: SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha256,
                                    default: true,
                                },
                                {
                                    label: "RSA-SHA384",
                                    value: SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha384,
                                },
                                {
                                    label: "RSA-SHA512",
                                    value: SignatureAlgorithmEnum.HttpWwwW3Org200104XmldsigMorersaSha512,
                                },
                                {
                                    label: "DSA-SHA1",
                                    value: SignatureAlgorithmEnum.HttpWwwW3Org200009XmldsigdsaSha1,
                                },
                            ]}
                            .value=${this.instance?.signatureAlgorithm}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
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
                            .certificate=${this.instance?.encryptionKp}
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When selected, encrypted assertions will be decrypted using this keypair.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group open label="${msg("SAML Attribute mapping")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="userPropertyMappings">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "userPropertyMappings",
                            },
                            msg("User Property Mappings"),
                        )}
                        <ak-dual-select-dynamic-selected
                            id="userPropertyMappings"
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.userPropertyMappings,
                            )}
                            available-label="${msg("Available User Property Mappings")}"
                            selected-label="${msg("Selected User Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for user creation.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="groupPropertyMappings">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "groupPropertyMappings",
                            },
                            msg("Group Property Mappings"),
                        )}
                        <ak-dual-select-dynamic-selected
                            id="groupPropertyMappings"
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.groupPropertyMappings,
                            )}
                            available-label="${msg("Available Group Property Mappings")}"
                            selected-label="${msg("Selected Group Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for group creation.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Flow settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="preAuthenticationFlow">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "preAuthenticationFlow",
                                required: true,
                            },
                            msg("Pre-authentication flow"),
                        )}
                        <ak-source-flow-search
                            id="preAuthenticationFlow"
                            flowType=${FlowDesignationEnum.StageConfiguration}
                            .currentFlow=${this.instance?.preAuthenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-pre-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow used before authentication.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="authenticationFlow">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "authenticationFlow",
                            },
                            msg("Authentication Flow"),
                        )}
                        <ak-source-flow-search
                            id="authenticationFlow"
                            flowType=${FlowDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.authenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="enrollmentFlow">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "enrollmentFlow",
                            },
                            msg("Enrollment flow"),
                        )}
                        <ak-source-flow-search
                            id="enrollmentFlow"
                            flowType=${FlowDesignationEnum.Enrollment}
                            .currentFlow=${this.instance?.enrollmentFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-enrollment"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when enrolling new users.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label=${msg("Advanced settings")}>
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="policyEngineMode">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "policyEngineMode",
                                required: true,
                            },
                            msg("Policy engine mode"),
                        )}
                        <ak-radio
                            id="policyEngineMode"
                            .options=${policyEngineModes}
                            .value=${this.instance?.policyEngineMode}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-saml-form": SAMLSourceForm;
    }
}
