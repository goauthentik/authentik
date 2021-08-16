import { CoreApi, FlowsApi, FlowsInstancesListDesignationEnum, Tenant } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/forms/FormGroup";
import { first } from "../../utils";
import { ModelForm } from "../../elements/forms/ModelForm";
import { until } from "lit-html/directives/until";
import { DefaultTenant } from "../../elements/sidebar/SidebarBrand";

@customElement("ak-tenant-form")
export class TenantForm extends ModelForm<Tenant, string> {
    loadInstance(pk: string): Promise<Tenant> {
        return new CoreApi(DEFAULT_CONFIG).coreTenantsRetrieve({
            tenantUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated tenant.`;
        } else {
            return t`Successfully created tenant.`;
        }
    }

    send = (data: Tenant): Promise<Tenant> => {
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
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Domain`} ?required=${true} name="domain">
                <input
                    type="text"
                    value="${first(this.instance?.domain, window.location.host)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Matching is done based on domain suffix, so if you enter domain.tld, foo.domain.tld will still match.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="_default">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?._default, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Default`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Use this tenant for each domain that doesn't have a dedicated tenant.`}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Branding settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Title`}
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
                            ${t`Branding shown in page title and several other places.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Logo`}
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
                            ${t`Icon shown in sidebar/header and flow executor.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Favicon`}
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
                        <p class="pf-c-form__helper-text">${t`Icon shown in the browser tab.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Default flows`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Authentication flow`}
                        name="flowAuthentication"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.flowAuthentication === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "pk",
                                        designation:
                                            FlowsInstancesListDesignationEnum.Authentication,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            const selected =
                                                this.instance?.flowAuthentication === flow.pk;
                                            return html`<option
                                                value=${flow.pk}
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
                            ${t`Flow used to authenticate users. If left empty, the first applicable flow sorted by the slug is used.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Invalidation flow`}
                        name="flowInvalidation"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.flowInvalidation === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "pk",
                                        designation: FlowsInstancesListDesignationEnum.Invalidation,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            const selected =
                                                this.instance?.flowInvalidation === flow.pk;
                                            return html`<option
                                                value=${flow.pk}
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
                            ${t`Flow used to logout. If left empty, the first applicable flow sorted by the slug is used.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Recovery flow`} name="flowRecovery">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.flowRecovery === undefined}>
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "pk",
                                        designation: FlowsInstancesListDesignationEnum.Recovery,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            const selected =
                                                this.instance?.flowRecovery === flow.pk;
                                            return html`<option
                                                value=${flow.pk}
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
                            ${t`Recovery flow. If left empty, the first applicable flow sorted by the slug is used.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Unenrollment flow`}
                        name="flowUnenrollment"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=""
                                ?selected=${this.instance?.flowUnenrollment === undefined}
                            >
                                ---------
                            </option>
                            ${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        ordering: "pk",
                                        designation: FlowsInstancesListDesignationEnum.Unenrollment,
                                    })
                                    .then((flows) => {
                                        return flows.results.map((flow) => {
                                            const selected =
                                                this.instance?.flowUnenrollment === flow.pk;
                                            return html`<option
                                                value=${flow.pk}
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
                            ${t`If set, users are able to unenroll themselves using this flow. If no flow is set, option is not shown.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Other global settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Event retention`}
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
                            ${t`Duration after which events will be deleted from the database.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`When using an external logging solution for archiving, this can be set to "minutes=5".`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`This setting only affects new Events, as the expiration is saved per-event.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Format: "weeks=3;days=2;hours=3,seconds=2".`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
