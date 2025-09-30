import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#elements/CodeMirror";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { DefaultBrand } from "#common/ui/config";

import { CodeMirrorMode } from "#elements/CodeMirror";
import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

import { certificateProvider, certificateSelector } from "#admin/brands/Certificates";

import {
    Application,
    Brand,
    CoreApi,
    CoreApplicationsListRequest,
    FlowsInstancesListDesignationEnum,
} from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

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
        data.attributes ??= {};
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

    public override renderForm(): TemplateResult {
        return html` <ak-text-input
                required
                name="domain"
                input-hint="code"
                placeholder="subdomain.example.com"
                value="${this.instance?.domain ?? window.location.host}"
                label=${msg("Domain")}
                help=${msg(
                    "Matching is done based on domain suffix, so if you enter domain.tld, foo.domain.tld will still match.",
                )}
            ></ak-text-input>

            <ak-switch-input
                name="_default"
                label=${msg("Sign assertions")}
                ?checked=${this.instance?._default ?? false}
                help=${msg("Use this brand for each domain that doesn't have a dedicated brand.")}
            >
            </ak-switch-input>

            <ak-form-group label="${msg("Branding settings")} ">
                <div class="pf-c-form">
                    <ak-text-input
                        required
                        name="brandingTitle"
                        placeholder="authentik"
                        value="${this.instance?.brandingTitle ?? DefaultBrand.brandingTitle}"
                        label=${msg("Title")}
                        autocomplete="off"
                        spellcheck="false"
                        help=${msg("Branding shown in page title and several other places.")}
                    ></ak-text-input>

                    <ak-text-input
                        required
                        name="brandingLogo"
                        input-hint="code"
                        placeholder="/static/dist/your-logo.svg"
                        value="${this.instance?.brandingLogo ?? DefaultBrand.brandingLogo}"
                        label=${msg("Logo")}
                        autocomplete="off"
                        spellcheck="false"
                        help=${msg("Logo shown in sidebar/header and flow executor.")}
                    ></ak-text-input>

                    <ak-text-input
                        required
                        name="brandingFavicon"
                        input-hint="code"
                        placeholder="/your-favicon.png"
                        value="${this.instance?.brandingFavicon ?? DefaultBrand.brandingFavicon}"
                        label=${msg("Favicon")}
                        autocomplete="off"
                        spellcheck="false"
                        help=${msg("Icon shown in the browser tab.")}
                    ></ak-text-input>

                    <ak-text-input
                        required
                        name="brandingDefaultFlowBackground"
                        input-hint="code"
                        placeholder="/your-favicon.png"
                        value="${this.instance?.brandingDefaultFlowBackground ??
                        "/static/dist/assets/images/flow_background.jpg"}"
                        label=${msg("Default flow background")}
                        autocomplete="off"
                        spellcheck="false"
                        help=${msg(
                            "Default background used during flow execution. Can be overridden per flow.",
                        )}
                    ></ak-text-input>

                    <ak-form-element-horizontal name="brandingCustomCss">
                        <div slot="label" class="pf-c-form__group-label">
                            ${AKLabel({ htmlFor: "branding-custom-css" }, msg("Custom CSS"))}
                        </div>

                        <ak-codemirror
                            id="branding-custom-css"
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

            <ak-form-group label="${msg("External user settings")} ">
                <div class="pf-c-form">
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

            <ak-form-group label="${msg("Default flows")} ">
                <div class="pf-c-form">
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
            <ak-form-group label="${msg("Other global settings")} ">
                <div class="pf-c-form">
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

                    <ak-form-element-horizontal name="attributes">
                        <div slot="label" class="pf-c-form__group-label">
                            ${AKLabel({ htmlFor: "attributes" }, msg("Attributes"))}
                        </div>
                        <ak-codemirror
                            id="attributes"
                            name="attributes"
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
