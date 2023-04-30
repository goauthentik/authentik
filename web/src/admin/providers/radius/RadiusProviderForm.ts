import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ascii_letters, digits, first, randomString } from "@goauthentik/common/utils";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement } from "lit/decorators.js";

import {
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    ProvidersApi,
    RadiusProvider,
} from "@goauthentik/api";

@customElement("ak-provider-radius-form")
export class RadiusProviderFormPage extends ModelForm<RadiusProvider, number> {
    loadInstance(pk: number): Promise<RadiusProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersRadiusRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
        }
    }

    async send(data: RadiusProvider): Promise<RadiusProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersRadiusUpdate({
                id: this.instance.pk || 0,
                radiusProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersRadiusCreate({
                radiusProviderRequest: data,
            });
        }
    }

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
            <ak-form-element-horizontal
                label=${t`Authentication flow`}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                        const args: FlowsInstancesListRequest = {
                            ordering: "slug",
                            designation: FlowsInstancesListDesignationEnum.Authentication,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
                        return flows.results;
                    }}
                    .renderElement=${(flow: Flow): string => {
                        return RenderFlowOption(flow);
                    }}
                    .renderDescription=${(flow: Flow): TemplateResult => {
                        return html`${flow.slug}`;
                    }}
                    .value=${(flow: Flow | undefined): string | undefined => {
                        return flow?.pk;
                    }}
                    .selected=${(flow: Flow): boolean => {
                        let selected = flow.pk === rootInterface()?.tenant?.flowAuthentication;
                        if (this.instance?.authorizationFlow === flow.pk) {
                            selected = true;
                        }
                        return selected;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">${t`Flow used for users to authenticate.`}</p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Shared secret`}
                        ?required=${true}
                        name="sharedSecret"
                    >
                        <input
                            type="text"
                            value="${first(
                                this.instance?.sharedSecret,
                                randomString(128, ascii_letters + digits),
                            )}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Client Networks`}
                        ?required=${true}
                        name="clientNetworks"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.clientNetworks, "0.0.0.0/0, ::/0")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`List of CIDRs (comma-seperated) that clients can connect from. A more specific
                            CIDR will match before a looser one. Clients connecting from a non-specified CIDR
                            will be dropped.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
