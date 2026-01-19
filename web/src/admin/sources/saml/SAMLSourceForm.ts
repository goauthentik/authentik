import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-source-flow-search";
import "#components/ak-file-search-input";
import "#components/ak-slug-input";
import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/utils/TimeDeltaHelp";

import { propertyMappingsProvider, propertyMappingsSelector } from "./SAMLSourceFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { type AkCryptoCertificateSearch } from "#admin/common/ak-crypto-certificate-search";
import { iconHelperText, placeholderHelperText } from "#admin/helperText";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { BaseSourceForm } from "#admin/sources/BaseSourceForm";
import { GroupMatchingModeToLabel, UserMatchingModeToLabel } from "#admin/sources/oauth/utils";

import {
    AdminFileListUsageEnum,
    BindingTypeEnum,
    DigestAlgorithmEnum,
    FlowsInstancesListDesignationEnum,
    GroupMatchingModeEnum,
    SAMLNameIDPolicyEnum,
    SAMLSource,
    SignatureAlgorithmEnum,
    SourcesApi,
    UserMatchingModeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-source-saml-form")
export class SAMLSourceForm extends BaseSourceForm<SAMLSource> {
    @state()
    hasSigningCert = false;

    reset(): void {
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

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>

            <ak-slug-input
                name="slug"
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
            <ak-form-element-horizontal
                label=${msg("User matching mode")}
                required
                name="userMatchingMode"
            >
                <select class="pf-c-form-control">
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
            <ak-form-element-horizontal
                label=${msg("Group matching mode")}
                required
                name="groupMatchingMode"
            >
                <select class="pf-c-form-control">
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
                .usage=${AdminFileListUsageEnum.Media}
                blankable
                help=${iconHelperText}
            ></ak-file-search-input>

            <ak-form-group open label="${msg("Protocol settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("SSO URL")} required name="ssoUrl">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.ssoUrl)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("URL that the initial Login request is sent to.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("SLO URL")} name="sloUrl">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.sloUrl || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Optional URL if the IDP supports Single-Logout.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Issuer")} name="issuer">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.issuer)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Also known as Entity ID. Defaults the Metadata URL.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Binding Type")}
                        required
                        name="bindingType"
                    >
                        <ak-radio
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
                    <ak-form-element-horizontal label=${msg("Signing keypair")} name="signingKp">
                        <ak-crypto-certificate-search
                            .certificate=${this.instance?.signingKp}
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Keypair which is used to sign outgoing requests. Leave empty to disable signing.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Verification Certificate")}
                        name="verificationKp"
                    >
                        <ak-crypto-certificate-search
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
                    <ak-form-element-horizontal
                        label=${msg("NameID Policy")}
                        required
                        name="nameIdPolicy"
                    >
                        <select class="pf-c-form-control">
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
                    <ak-form-element-horizontal label=${msg("User path")} name="userPathTemplate">
                        <input
                            type="text"
                            value="${this.instance?.userPathTemplate ??
                            "goauthentik.io/sources/%(slug)s"}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">${placeholderHelperText}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Delete temporary users after")}
                        required
                        name="temporaryUserDeleteAfter"
                    >
                        <input
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
                    <ak-form-element-horizontal
                        label=${msg("Digest algorithm")}
                        required
                        name="digestAlgorithm"
                    >
                        <ak-radio
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
                    <ak-form-element-horizontal
                        label=${msg("Signature algorithm")}
                        required
                        name="signatureAlgorithm"
                    >
                        <ak-radio
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
                    <ak-form-element-horizontal
                        label=${msg("Encryption Certificate")}
                        name="encryptionKp"
                    >
                        <ak-crypto-certificate-search
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
                    <ak-form-element-horizontal
                        label=${msg("User Property Mappings")}
                        name="userPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
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
                    <ak-form-element-horizontal
                        label=${msg("Group Property Mappings")}
                        name="groupPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
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
                    <ak-form-element-horizontal
                        label=${msg("Pre-authentication flow")}
                        required
                        name="preAuthenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.StageConfiguration}
                            .currentFlow=${this.instance?.preAuthenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-pre-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow used before authentication.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
                        name="authenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.authenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
                        name="enrollmentFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Enrollment}
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
                    <ak-form-element-horizontal
                        label=${msg("Policy engine mode")}
                        required
                        name="policyEngineMode"
                    >
                        <ak-radio
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
