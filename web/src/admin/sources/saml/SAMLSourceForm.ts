import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
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

@customElement("ak-source-saml-form")
export class SAMLSourceForm extends ModelForm<SAMLSource, string> {
    loadInstance(pk: string): Promise<SAMLSource> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesSamlRetrieve({
            slug: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated source.");
        } else {
            return msg("Successfully created source.");
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
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
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
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <label class="pf-c-check__label"> ${msg("Enabled")} </label>
                </div>
            </ak-form-element-horizontal>

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
                        <select class="pf-c-form-control">
                            <option
                                value=${BindingTypeEnum.Redirect}
                                ?selected=${this.instance?.bindingType === BindingTypeEnum.Redirect}
                            >
                                ${msg("Redirect binding")}
                            </option>
                            <option
                                value=${BindingTypeEnum.PostAuto}
                                ?selected=${this.instance?.bindingType === BindingTypeEnum.PostAuto}
                            >
                                ${msg("Post binding (auto-submit)")}
                            </option>
                            <option
                                value=${BindingTypeEnum.Post}
                                ?selected=${this.instance?.bindingType === BindingTypeEnum.Post}
                            >
                                ${msg("Post binding")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Signing keypair")} name="signingKp">
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
                                html`<option
                                    value=${ifDefined(this.instance?.signingKp || undefined)}
                                    ?selected=${this.instance?.signingKp !== undefined}
                                >
                                    ${msg("Loading...")}
                                </option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Keypair which is used to sign outgoing requests. Leave empty to disable signing.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Advanced protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="allowIdpInitiated">
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.allowIdpInitiated, false)}
                            />
                            <label class="pf-c-check__label">
                                ${msg(" Allow IDP-initiated logins")}
                            </label>
                        </div>
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
                                value=${NameIdPolicyEnum._20nameidFormatpersistent}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._20nameidFormatpersistent}
                            >
                                ${msg("Persistent")}
                            </option>
                            <option
                                value=${NameIdPolicyEnum._11nameidFormatemailAddress}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._11nameidFormatemailAddress}
                            >
                                ${msg("Email address")}
                            </option>
                            <option
                                value=${NameIdPolicyEnum._20nameidFormatWindowsDomainQualifiedName}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._20nameidFormatWindowsDomainQualifiedName}
                            >
                                ${msg("Windows")}
                            </option>
                            <option
                                value=${NameIdPolicyEnum._20nameidFormatX509SubjectName}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._20nameidFormatX509SubjectName}
                            >
                                ${msg("X509 Subject")}
                            </option>
                            <option
                                value=${NameIdPolicyEnum._20nameidFormattransient}
                                ?selected=${this.instance?.nameIdPolicy ===
                                NameIdPolicyEnum._20nameidFormattransient}
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
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Path template for users created. Use placeholders like `%(slug)s` to insert the source slug.",
                            )}
                        </p>
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
                        <select class="pf-c-form-control">
                            <option
                                value=${DigestAlgorithmEnum._200009Xmldsigsha1}
                                ?selected=${this.instance?.digestAlgorithm ===
                                DigestAlgorithmEnum._200009Xmldsigsha1}
                            >
                                ${msg("SHA1")}
                            </option>
                            <option
                                value=${DigestAlgorithmEnum._200104Xmlencsha256}
                                ?selected=${this.instance?.digestAlgorithm ===
                                    DigestAlgorithmEnum._200104Xmlencsha256 ||
                                this.instance?.digestAlgorithm === undefined}
                            >
                                ${msg("SHA256")}
                            </option>
                            <option
                                value=${DigestAlgorithmEnum._200104XmldsigMoresha384}
                                ?selected=${this.instance?.digestAlgorithm ===
                                DigestAlgorithmEnum._200104XmldsigMoresha384}
                            >
                                ${msg("SHA384")}
                            </option>
                            <option
                                value=${DigestAlgorithmEnum._200104Xmlencsha512}
                                ?selected=${this.instance?.digestAlgorithm ===
                                DigestAlgorithmEnum._200104Xmlencsha512}
                            >
                                ${msg("SHA512")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Signature algorithm")}
                        ?required=${true}
                        name="signatureAlgorithm"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${SignatureAlgorithmEnum._200009XmldsigrsaSha1}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                SignatureAlgorithmEnum._200009XmldsigrsaSha1}
                            >
                                ${msg("RSA-SHA1")}
                            </option>
                            <option
                                value=${SignatureAlgorithmEnum._200104XmldsigMorersaSha256}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                    SignatureAlgorithmEnum._200104XmldsigMorersaSha256 ||
                                this.instance?.signatureAlgorithm === undefined}
                            >
                                ${msg("RSA-SHA256")}
                            </option>
                            <option
                                value=${SignatureAlgorithmEnum._200104XmldsigMorersaSha384}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                SignatureAlgorithmEnum._200104XmldsigMorersaSha384}
                            >
                                ${msg("RSA-SHA384")}
                            </option>
                            <option
                                value=${SignatureAlgorithmEnum._200104XmldsigMorersaSha512}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                SignatureAlgorithmEnum._200104XmldsigMorersaSha512}
                            >
                                ${msg("RSA-SHA512")}
                            </option>
                            <option
                                value=${SignatureAlgorithmEnum._200009XmldsigdsaSha1}
                                ?selected=${this.instance?.signatureAlgorithm ===
                                SignatureAlgorithmEnum._200009XmldsigdsaSha1}
                            >
                                ${msg("DSA-SHA1")}
                            </option>
                        </select>
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
                                html`<option>${msg("Loading...")}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow used before authentication.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
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
                                html`<option>${msg("Loading...")}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
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
                                html`<option>${msg("Loading...")}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when enrolling new users.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
