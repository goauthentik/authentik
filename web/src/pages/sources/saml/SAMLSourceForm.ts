import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    BindingTypeEnum,
    CryptoApi,
    DigestAlgorithmEnum,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    NameIdPolicyEnum,
    SAMLSource,
    SignatureAlgorithmEnum,
    SourcesApi,
} from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";
import "../../../elements/utils/TimeDeltaHelp";
import { first } from "../../../utils";

@customElement("ak-source-saml-form")
export class SAMLSourceForm extends ModelForm<SAMLSource, string> {
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

    send = (data: SAMLSource): Promise<SAMLSource> => {
        if (this.instance) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesSamlUpdate({
                slug: this.instance.slug,
                sAMLSourceRequest: data,
            });
        } else {
            return new SourcesApi(DEFAULT_CONFIG).sourcesSamlCreate({
                sAMLSourceRequest: data,
            });
        }
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
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.signingKp === undefined}>
                                ---------
                            </option>
                            ${until(
                                new CryptoApi(DEFAULT_CONFIG)
                                    .cryptoCertificatekeypairsList({
                                        ordering: "name",
                                    })
                                    .then((keys) => {
                                        return keys.results.map((key) => {
                                            return html`<option
                                                value=${ifDefined(key.pk)}
                                                ?selected=${this.instance?.signingKp === key.pk}
                                            >
                                                ${key.name}
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
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
