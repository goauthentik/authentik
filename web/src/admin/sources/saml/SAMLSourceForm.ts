import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-source-flow-search";
import { iconHelperText, placeholderHelperText } from "@goauthentik/admin/helperText";
import { BaseSourceForm } from "@goauthentik/admin/sources/BaseSourceForm";
import {
    GroupMatchingModeToLabel,
    UserMatchingModeToLabel,
} from "@goauthentik/admin/sources/oauth/utils";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import {
    CapabilitiesEnum,
    WithCapabilitiesConfig,
} from "@goauthentik/elements/Interface/capabilitiesProvider";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    BindingTypeEnum,
    DigestAlgorithmEnum,
    FlowsInstancesListDesignationEnum,
    GroupMatchingModeEnum,
    NameIdPolicyEnum,
    SAMLSource,
    SignatureAlgorithmEnum,
    SourcesApi,
    UserMatchingModeEnum,
} from "@goauthentik/api";

import { propertyMappingsProvider, propertyMappingsSelector } from "./SAMLSourceFormHelpers.js";

@customElement("ak-source-saml-form")
export class SAMLSourceForm extends WithCapabilitiesConfig(BaseSourceForm<SAMLSource>) {
    @state()
    clearIcon = false;

    async loadInstance(pk: string): Promise<SAMLSource> {
        const source = await new SourcesApi(DEFAULT_CONFIG).sourcesSamlRetrieve({
            slug: pk,
        });
        this.clearIcon = false;
        return source;
    }

    async send(data: SAMLSource): Promise<SAMLSource> {
        let source: SAMLSource;
        if (this.instance) {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesSamlUpdate({
                slug: this.instance.slug,
                sAMLSourceRequest: data,
            });
        } else {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesSamlCreate({
                sAMLSourceRequest: data,
            });
        }
        const c = await config();
        if (c.capabilities.includes(CapabilitiesEnum.CanSaveMedia)) {
            const icon = this.getFormFiles()["icon"];
            if (icon || this.clearIcon) {
                await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconCreate({
                    slug: source.slug,
                    file: icon,
                    clear: this.clearIcon,
                });
            }
        } else {
            await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconUrlCreate({
                slug: source.slug,
                filePathRequest: {
                    url: data.icon || "",
                },
            });
        }
        return source;
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Slug")} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Enabled")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("User matching mode")}
                ?required=${true}
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
                ?required=${true}
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
            ${this.can(CapabilitiesEnum.CanSaveMedia)
                ? html`<ak-form-element-horizontal label=${msg("Icon")} name="icon">
                          <input type="file" value="" class="pf-c-form-control" />
                          ${this.instance?.icon
                              ? html`
                                    <p class="pf-c-form__helper-text">
                                        ${msg("Currently set to:")} ${this.instance?.icon}
                                    </p>
                                `
                              : html``}
                      </ak-form-element-horizontal>
                      ${this.instance?.icon
                          ? html`
                                <ak-form-element-horizontal>
                                    <label class="pf-c-switch">
                                        <input
                                            class="pf-c-switch__input"
                                            type="checkbox"
                                            @change=${(ev: Event) => {
                                                const target = ev.target as HTMLInputElement;
                                                this.clearIcon = target.checked;
                                            }}
                                        />
                                        <span class="pf-c-switch__toggle">
                                            <span class="pf-c-switch__toggle-icon">
                                                <i class="fas fa-check" aria-hidden="true"></i>
                                            </span>
                                        </span>
                                        <span class="pf-c-switch__label">
                                            ${msg("Clear icon")}
                                        </span>
                                    </label>
                                    <p class="pf-c-form__helper-text">
                                        ${msg("Delete currently set icon.")}
                                    </p>
                                </ak-form-element-horizontal>
                            `
                          : html``}`
                : html`<ak-form-element-horizontal label=${msg("Icon")} name="icon">
                      <input
                          type="text"
                          value="${first(this.instance?.icon, "")}"
                          class="pf-c-form-control"
                      />
                      <p class="pf-c-form__helper-text">${iconHelperText}</p>
                  </ak-form-element-horizontal>`}

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("SSO URL")}
                        ?required=${true}
                        name="ssoUrl"
                    >
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
                        ?required=${true}
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
                            nokey
                        ></ak-crypto-certificate-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When selected, incoming assertion's Signatures will be validated against this certificate. To allow unsigned Requests, leave on default.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Advanced protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="allowIdpInitiated">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.allowIdpInitiated, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg(" Allow IDP-initiated logins")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Allows authentication flows initiated by the IdP. This can be a security risk, as no validation of the request ID is done.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("NameID Policy")}
                        ?required=${true}
                        name="nameIdPolicy"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${NameIdPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum.UrnOasisNamesTcSaml20NameidFormatPersistent}
                            >
                                ${msg("Persistent")}
                            </option>
                            <option
                                value=${NameIdPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum.UrnOasisNamesTcSaml11NameidFormatEmailAddress}
                            >
                                ${msg("Email address")}
                            </option>
                            <option
                                value=${NameIdPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum.UrnOasisNamesTcSaml20NameidFormatWindowsDomainQualifiedName}
                            >
                                ${msg("Windows")}
                            </option>
                            <option
                                value=${NameIdPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum.UrnOasisNamesTcSaml11NameidFormatX509SubjectName}
                            >
                                ${msg("X509 Subject")}
                            </option>
                            <option
                                value=${NameIdPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum.UrnOasisNamesTcSaml20NameidFormatTransient}
                            >
                                ${msg("Transient")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("User path")} name="userPathTemplate">
                        <input
                            type="text"
                            value="${first(
                                this.instance?.userPathTemplate,
                                "goauthentik.io/sources/%(slug)s",
                            )}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">${placeholderHelperText}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Delete temporary users after")}
                        ?required=${true}
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
                        ?required=${true}
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
                        ?required=${true}
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
            <ak-form-group ?expanded=${true}>
                <span slot="header"> ${msg("SAML Attribute mapping")} </span>
                <div slot="body" class="pf-c-form">
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
            <ak-form-group>
                <span slot="header"> ${msg("Flow settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Pre-authentication flow")}
                        ?required=${true}
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
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-saml-form": SAMLSourceForm;
    }
}
