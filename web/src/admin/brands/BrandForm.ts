import { certificateProvider, certificateSelector } from "@goauthentik/admin/brands/Certificates";
import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { DefaultBrand } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import {
    Application,
    Brand,
    CoreApi,
    CoreApplicationsListRequest,
    FlowsInstancesListDesignationEnum,
} from "@goauthentik/api";

@customElement("ak-brand-form")
export class BrandForm extends ModelForm<Brand, string> {
    loadInstance(pk: string): Promise<Brand> {
        return new CoreApi(DEFAULT_CONFIG).coreBrandsRetrieve({
            brandUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated brand.")
            : msg("Successfully created brand.");
    }

    async send(data: Brand): Promise<Brand> {
        if (this.instance?.brandUuid) {
            return new CoreApi(DEFAULT_CONFIG).coreBrandsUpdate({
                brandUuid: this.instance.brandUuid,
                brandRequest: data,
            });
        }
        return new CoreApi(DEFAULT_CONFIG).coreBrandsCreate({
            brandRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Domain")} required name="domain">
                <input
                    type="text"
                    value="${this.instance?.domain ?? window.location.host}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    inputmode="url"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Matching is done based on domain suffix, so if you enter domain.tld, foo.domain.tld will still match.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="_default">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?._default ?? false}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Default")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("Use this brand for each domain that doesn't have a dedicated brand.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group>
                <span slot="header"> ${msg("Branding settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Title")} required name="brandingTitle">
                        <input
                            type="text"
                            value="${this.instance?.brandingTitle ?? DefaultBrand.brandingTitle}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Branding shown in page title and several other places.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Logo")} required name="brandingLogo">
                        <input
                            type="text"
                            value="${this.instance?.brandingLogo ?? DefaultBrand.brandingLogo}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Icon shown in sidebar/header and flow executor.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Favicon")}
                        required
                        name="brandingFavicon"
                    >
                        <input
                            type="text"
                            value="${this.instance?.brandingFavicon ??
                            DefaultBrand.brandingFavicon}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Icon shown in the browser tab.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Default flow background")}
                        ?required=${true}
                        name="brandingDefaultFlowBackground"
                    >
                        <input
                            type="text"
                            value="${this.instance?.brandingDefaultFlowBackground ??
                            "/static/dist/assets/images/flow_background.jpg"}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Default background used during flow execution. Can be overridden per flow.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Custom CSS")}
                        required
                        name="brandingCustomCss"
                    >
                        <ak-codemirror
                            mode=${CodeMirrorMode.CSS}
                            value="${this.instance?.brandingCustomCss ??
                            DefaultBrand.brandingCustomCss}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Custom CSS to apply to pages when this brand is active.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header"> ${msg("External user settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Default application")}
                        name="defaultApplication"
                    >
                        <ak-search-select
                            blankable
                            .fetchObjects=${async (query?: string): Promise<Application[]> => {
                                const args: CoreApplicationsListRequest = {
                                    ordering: "name",
                                    superuserFullList: true,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const users = await new CoreApi(
                                    DEFAULT_CONFIG,
                                ).coreApplicationsList(args);
                                return users.results;
                            }}
                            .renderElement=${(item: Application): string => {
                                return item.name;
                            }}
                            .renderDescription=${(item: Application): TemplateResult => {
                                return html`${item.slug}`;
                            }}
                            .value=${(item: Application | undefined): string | undefined => {
                                return item?.pk;
                            }}
                            .selected=${(item: Application): boolean => {
                                return item.pk === this.instance?.defaultApplication;
                            }}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When configured, external users will automatically be redirected to this application when not attempting to access a different application",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group>
                <span slot="header"> ${msg("Default flows")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
                        name="flowAuthentication"
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.flowAuthentication}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used to authenticate users. If left empty, the first applicable flow sorted by the slug is used.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Invalidation flow")}
                        name="flowInvalidation"
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                            .currentFlow=${this.instance?.flowInvalidation}
                        ></ak-flow-search>

                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used to logout. If left empty, the first applicable flow sorted by the slug is used.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Recovery flow")} name="flowRecovery">
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Recovery}
                            .currentFlow=${this.instance?.flowRecovery}
                        ></ak-flow-search>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Unenrollment flow")}
                        name="flowUnenrollment"
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Unenrollment}
                            .currentFlow=${this.instance?.flowUnenrollment}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If set, users are able to unenroll themselves using this flow. If no flow is set, option is not shown.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("User settings flow")}
                        name="flowUserSettings"
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.StageConfiguration}
                            .currentFlow=${this.instance?.flowUserSettings}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("If set, users are able to configure details of their profile.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Device code flow")}
                        name="flowDeviceCode"
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.StageConfiguration}
                            .currentFlow=${this.instance?.flowDeviceCode}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If set, the OAuth Device Code profile can be used, and the selected flow will be used to enter the code.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Other global settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Web Certificate")}
                        name="webCertificate"
                    >
                        <ak-crypto-certificate-search
                            .certificate=${this.instance?.webCertificate}
                        ></ak-crypto-certificate-search>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Client Certificates")}
                        name="clientCertificates"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${certificateProvider}
                            .selector=${certificateSelector(this.instance?.clientCertificates)}
                            available-label=${msg("Available Certificates")}
                            selected-label=${msg("Selected Certificates")}
                        ></ak-dual-select-dynamic-selected>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Attributes")} name="attributes">
                        <ak-codemirror
                            mode=${CodeMirrorMode.YAML}
                            value="${YAML.stringify(this.instance?.attributes ?? {})}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Set custom attributes using YAML or JSON. Any attributes set here will be inherited by users, if the request is handled by this brand.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-form": BrandForm;
    }
}
