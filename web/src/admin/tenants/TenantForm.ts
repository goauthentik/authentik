import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import { DefaultTenant } from "@goauthentik/elements/sidebar/SidebarBrand";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { CoreApi, FlowsInstancesListDesignationEnum, Tenant } from "@goauthentik/api";

@customElement("ak-tenant-form")
export class TenantForm extends ModelForm<Tenant, string> {
    loadInstance(pk: string): Promise<Tenant> {
        return new CoreApi(DEFAULT_CONFIG).coreTenantsRetrieve({
            tenantUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated tenant.");
        } else {
            return msg("Successfully created tenant.");
        }
    }

    async send(data: Tenant): Promise<Tenant> {
        if (this.instance?.tenantUuid) {
            return new CoreApi(DEFAULT_CONFIG).coreTenantsUpdate({
                tenantUuid: this.instance.tenantUuid,
                tenantRequest: data,
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreTenantsCreate({
                tenantRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Domain")} ?required=${true} name="domain">
                <input
                    type="text"
                    value="${first(this.instance?.domain, window.location.host)}"
                    class="pf-c-form-control"
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
                        ?checked=${first(this.instance?._default, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Default")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("Use this tenant for each domain that doesn't have a dedicated tenant.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Branding settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Title")}
                        ?required=${true}
                        name="brandingTitle"
                    >
                        <input
                            type="text"
                            value="${first(
                                this.instance?.brandingTitle,
                                DefaultTenant.brandingTitle,
                            )}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Branding shown in page title and several other places.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Logo")}
                        ?required=${true}
                        name="brandingLogo"
                    >
                        <input
                            type="text"
                            value="${first(
                                this.instance?.brandingLogo,
                                DefaultTenant.brandingLogo,
                            )}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Icon shown in sidebar/header and flow executor.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Favicon")}
                        ?required=${true}
                        name="brandingFavicon"
                    >
                        <input
                            type="text"
                            value="${first(
                                this.instance?.brandingFavicon,
                                DefaultTenant.brandingFavicon,
                            )}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Icon shown in the browser tab.")}
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
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Recovery flow. If left empty, the first applicable flow sorted by the slug is used.",
                            )}
                        </p>
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
                            certificate=${this.instance?.webCertificate}
                        ></ak-crypto-certificate-search>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Event retention")}
                        ?required=${true}
                        name="eventRetention"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.eventRetention, "days=365")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Duration after which events will be deleted from the database.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                'When using an external logging solution for archiving, this can be set to "minutes=5".',
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "This setting only affects new Events, as the expiration is saved per-event.",
                            )}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg('Format: "weeks=3;days=2;hours=3,seconds=2".')}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Attributes")} name="attributes">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(first(this.instance?.attributes, {}))}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Set custom attributes using YAML or JSON. Any attributes set here will be inherited by users, if the request is handled by this tenant.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
