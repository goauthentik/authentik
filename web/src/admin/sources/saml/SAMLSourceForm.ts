import { UserMatchingModeToLabel } from "@goauthentik/admin/sources/oauth/utils";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    BindingTypeEnum,
    CapabilitiesEnum,
    CertificateKeyPair,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    DigestAlgorithmEnum,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    NameIdPolicyEnum,
    SAMLSource,
    SignatureAlgorithmEnum,
    SourcesApi,
    UserMatchingModeEnum,
} from "@goauthentik/api";

@customElement("ak-source-saml-form")
export class SAMLSourceForm extends ModelForm<SAMLSource, string> {
    @state()
    clearIcon = false;

    loadInstance(pk: string): Promise<SAMLSource> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesSamlRetrieve({
            slug: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated source.`;
        } else {
            return t`Successfully created source.`;
        }
    }

    send = async (data: SAMLSource): Promise<SAMLSource> => {
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
        if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
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
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Slug`} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <label class="pf-c-check__label"> ${t`Enabled`} </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`User matching mode`}
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
            ${until(
                config().then((c) => {
                    if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
                        return html`<ak-form-element-horizontal label=${t`Icon`} name="icon">
                                <input type="file" value="" class="pf-c-form-control" />
                                ${this.instance?.icon
                                    ? html`
                                          <p class="pf-c-form__helper-text">
                                              ${t`Currently set to:`} ${this.instance?.icon}
                                          </p>
                                      `
                                    : html``}
                            </ak-form-element-horizontal>
                            ${this.instance?.icon
                                ? html`
                                      <ak-form-element-horizontal>
                                          <div class="pf-c-check">
                                              <input
                                                  type="checkbox"
                                                  class="pf-c-check__input"
                                                  @change=${(ev: Event) => {
                                                      const target = ev.target as HTMLInputElement;
                                                      this.clearIcon = target.checked;
                                                  }}
                                              />
                                              <label class="pf-c-check__label">
                                                  ${t`Clear icon`}
                                              </label>
                                          </div>
                                          <p class="pf-c-form__helper-text">
                                              ${t`Delete currently set icon.`}
                                          </p>
                                      </ak-form-element-horizontal>
                                  `
                                : html``}`;
                    }
                    return html`<ak-form-element-horizontal label=${t`Icon`} name="icon">
                        <input
                            type="text"
                            value="${first(this.instance?.icon, "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Either input a full URL, a relative path, or use 'fa://fa-test' to use the Font Awesome icon "fa-test".`}
                        </p>
                    </ak-form-element-horizontal>`;
                }),
            )}

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`SSO URL`} ?required=${true} name="ssoUrl">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.ssoUrl)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`URL that the initial Login request is sent to.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`SLO URL`} name="sloUrl">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.sloUrl || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Optional URL if the IDP supports Single-Logout.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Issuer`} name="issuer">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.issuer)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Also known as Entity ID. Defaults the Metadata URL.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Binding Type`}
                        ?required=${true}
                        name="bindingType"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${BindingTypeEnum.Redirect}
                                ?selected=${this.instance?.bindingType === BindingTypeEnum.Redirect}
                            >
                                ${t`Redirect binding`}
                            </option>
                            <option
                                value=${BindingTypeEnum.PostAuto}
                                ?selected=${this.instance?.bindingType === BindingTypeEnum.PostAuto}
                            >
                                ${t`Post binding (auto-submit)`}
                            </option>
                            <option
                                value=${BindingTypeEnum.Post}
                                ?selected=${this.instance?.bindingType === BindingTypeEnum.Post}
                            >
                                ${t`Post binding`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Signing keypair`} name="signingKp">
                        <ak-search-select
                            .fetchObjects=${async (
                                query?: string,
                            ): Promise<CertificateKeyPair[]> => {
                                const args: CryptoCertificatekeypairsListRequest = {
                                    ordering: "name",
                                    hasKey: true,
                                    includeDetails: false,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const certificates = await new CryptoApi(
                                    DEFAULT_CONFIG,
                                ).cryptoCertificatekeypairsList(args);
                                return certificates.results;
                            }}
                            .renderElement=${(item: CertificateKeyPair): string => {
                                return item.name;
                            }}
                            .value=${(item: CertificateKeyPair | undefined): string | undefined => {
                                return item?.pk;
                            }}
                            .selected=${(item: CertificateKeyPair): boolean => {
                                return item.pk === this.instance?.signingKp;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Keypair which is used to sign outgoing requests. Leave empty to disable signing.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Advanced protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="allowIdpInitiated">
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.allowIdpInitiated, false)}
                            />
                            <label class="pf-c-check__label">
                                ${t` Allow IDP-initiated logins`}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${t`Allows authentication flows initiated by the IdP. This can be a security risk, as no validation of the request ID is done.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`NameID Policy`}
                        ?required=${true}
                        name="nameIdPolicy"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${NameIdPolicyEnum._20nameidFormatpersistent}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._20nameidFormatpersistent}
                            >
                                ${t`Persistent`}
                            </option>
                            <option
                                value=${NameIdPolicyEnum._11nameidFormatemailAddress}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._11nameidFormatemailAddress}
                            >
                                ${t`Email address`}
                            </option>
                            <option
                                value=${NameIdPolicyEnum._20nameidFormatWindowsDomainQualifiedName}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._20nameidFormatWindowsDomainQualifiedName}
                            >
                                ${t`Windows`}
                            </option>
                            <option
                                value=${NameIdPolicyEnum._20nameidFormatX509SubjectName}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._20nameidFormatX509SubjectName}
                            >
                                ${t`X509 Subject`}
                            </option>
                            <option
                                value=${NameIdPolicyEnum._20nameidFormattransient}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._20nameidFormattransient}
                            >
                                ${t`Transient`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`User path`} name="userPathTemplate">
                        <input
                            type="text"
                            value="${first(
                                this.instance?.userPathTemplate,
                                "goauthentik.io/sources/%(slug)s",
                            )}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Path template for users created. Use placeholders like \`%(slug)s\` to insert the source slug.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Delete temporary users after`}
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
                            ${t`Time offset when temporary users should be deleted. This only applies if your IDP uses the NameID Format 'transient', and the user doesn't log out manually.`}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Digest algorithm`}
                        ?required=${true}
                        name="digestAlgorithm"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${DigestAlgorithmEnum._200009Xmldsigsha1}
                                ?selected=${this.instance?.digestAlgorithm ===
                                DigestAlgorithmEnum._200009Xmldsigsha1}
                            >
                                ${t`SHA1`}
                            </option>
                            <option
                                value=${DigestAlgorithmEnum._200104Xmlencsha256}
                                ?selected=${this.instance?.digestAlgorithm ===
                                    DigestAlgorithmEnum._200104Xmlencsha256 ||
                                this.instance?.digestAlgorithm === undefined}
                            >
                                ${t`SHA256`}
                            </option>
                            <option
                                value=${DigestAlgorithmEnum._200104XmldsigMoresha384}
                                ?selected=${this.instance?.digestAlgorithm ===
                                DigestAlgorithmEnum._200104XmldsigMoresha384}
                            >
                                ${t`SHA384`}
                            </option>
                            <option
                                value=${DigestAlgorithmEnum._200104Xmlencsha512}
                                ?selected=${this.instance?.digestAlgorithm ===
                                DigestAlgorithmEnum._200104Xmlencsha512}
                            >
                                ${t`SHA512`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Signature algorithm`}
                        ?required=${true}
                        name="signatureAlgorithm"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${SignatureAlgorithmEnum._200009XmldsigrsaSha1}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                SignatureAlgorithmEnum._200009XmldsigrsaSha1}
                            >
                                ${t`RSA-SHA1`}
                            </option>
                            <option
                                value=${SignatureAlgorithmEnum._200104XmldsigMorersaSha256}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                    SignatureAlgorithmEnum._200104XmldsigMorersaSha256 ||
                                this.instance?.signatureAlgorithm === undefined}
                            >
                                ${t`RSA-SHA256`}
                            </option>
                            <option
                                value=${SignatureAlgorithmEnum._200104XmldsigMorersaSha384}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                SignatureAlgorithmEnum._200104XmldsigMorersaSha384}
                            >
                                ${t`RSA-SHA384`}
                            </option>
                            <option
                                value=${SignatureAlgorithmEnum._200104XmldsigMorersaSha512}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                SignatureAlgorithmEnum._200104XmldsigMorersaSha512}
                            >
                                ${t`RSA-SHA512`}
                            </option>
                            <option
                                value=${SignatureAlgorithmEnum._200009XmldsigdsaSha1}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                SignatureAlgorithmEnum._200009XmldsigdsaSha1}
                            >
                                ${t`DSA-SHA1`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Flow settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Pre-authentication flow`}
                        ?required=${true}
                        name="preAuthenticationFlow"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.preAuthenticationFlow === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "slug",
                                        designation:
                                            FlowsInstancesListDesignationEnum.StageConfiguration,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            let selected =
                                                this.instance?.preAuthenticationFlow === flow.pk;
                                            if (
                                                !this.instance?.pk &&
                                                !this.instance?.preAuthenticationFlow &&
                                                flow.slug === "default-source-pre-authentication"
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(flow.pk)}
                                                ?selected=${selected}
                                            >
                                                ${flow.name} (${flow.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Flow used before authentication.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Authentication flow`}
                        ?required=${true}
                        name="authenticationFlow"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.authenticationFlow === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "slug",
                                        designation:
                                            FlowsInstancesListDesignationEnum.Authentication,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            let selected =
                                                this.instance?.authenticationFlow === flow.pk;
                                            if (
                                                !this.instance?.pk &&
                                                !this.instance?.authenticationFlow &&
                                                flow.slug === "default-source-authentication"
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(flow.pk)}
                                                ?selected=${selected}
                                            >
                                                ${flow.name} (${flow.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Flow to use when authenticating existing users.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Enrollment flow`}
                        ?required=${true}
                        name="enrollmentFlow"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.enrollmentFlow === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "slug",
                                        designation: FlowsInstancesListDesignationEnum.Enrollment,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            let selected =
                                                this.instance?.enrollmentFlow === flow.pk;
                                            if (
                                                !this.instance?.pk &&
                                                !this.instance?.enrollmentFlow &&
                                                flow.slug === "default-source-enrollment"
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(flow.pk)}
                                                ?selected=${selected}
                                            >
                                                ${flow.name} (${flow.slug})
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Flow to use when enrolling new users.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
