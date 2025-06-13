import { certificateProvider, certificateSelector } from "@goauthentik/admin/brands/Certificates";
import "@goauthentik/admin/common/ak-crypto-certificate-search";
import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CertAttributeEnum,
    MutualTLSStage,
    MutualTLSStageModeEnum,
    StagesApi,
    UserAttributeEnum,
} from "@goauthentik/api";

@customElement("ak-stage-mtls-form")
export class MTLSStageForm extends BaseStageForm<MutualTLSStage> {
    loadInstance(pk: string): Promise<MutualTLSStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesMtlsRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: MutualTLSStage): Promise<MutualTLSStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesMtlsUpdate({
                stageUuid: this.instance.pk || "",
                mutualTLSStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesMtlsCreate({
                mutualTLSStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`
            <span> ${msg("Client-certificate/mTLS authentication/enrollment.")} </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Mode")} required name="mode">
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Certificate optional"),
                                    value: MutualTLSStageModeEnum.Optional,
                                    default: true,
                                    description: html`${msg(
                                        "If no certificate was provided, this stage will succeed and continue to the next stage.",
                                    )}`,
                                },
                                {
                                    label: msg("Certificate required"),
                                    value: MutualTLSStageModeEnum.Required,
                                    description: html`${msg(
                                        "If no certificate was provided, this stage will stop flow execution.",
                                    )}`,
                                },
                            ]}
                            .value=${this.instance?.mode}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Certificate authorities")}
                        name="certificateAuthorities"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${certificateProvider}
                            .selector=${certificateSelector(this.instance?.certificateAuthorities)}
                            available-label=${msg("Available Certificates")}
                            selected-label=${msg("Selected Certificates")}
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure the certificate authority client certificates are validated against. The certificate authority can also be configured on a brand, which allows for different certificate authorities for different domains.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Certificate attribute")}
                        required
                        name="certAttribute"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Common Name"),
                                    value: CertAttributeEnum.CommonName,
                                },
                                {
                                    label: msg("Email"),
                                    value: CertAttributeEnum.Email,
                                    default: true,
                                },
                                {
                                    label: msg("Subject"),
                                    value: CertAttributeEnum.Subject,
                                },
                            ]}
                            .value=${this.instance?.certAttribute}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure the attribute of the certificate used to look for a user.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("User attribute")}
                        required
                        name="userAttribute"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Username"),
                                    value: UserAttributeEnum.Username,
                                },
                                {
                                    label: msg("Email"),
                                    value: UserAttributeEnum.Email,
                                    default: true,
                                },
                            ]}
                            .value=${this.instance?.userAttribute}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${msg("Configure the attribute of the user used to look for a user.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-mtls-form": MTLSStageForm;
    }
}
