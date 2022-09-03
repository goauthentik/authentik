import { t } from "@lingui/macro";

import { customElement } from "lit-element";
import { TemplateResult, html } from "lit-html";
import { ifDefined } from "lit-html/directives/if-defined";
import { until } from "lit-html/directives/until";

import {
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    ProvidersApi,
    RadiusProvider,
} from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";
import { first, randomString } from "../../../utils";

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

    send = (data: RadiusProvider): Promise<RadiusProvider> => {
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
            <ak-form-element-horizontal
                label=${t`Authentication flow`}
                ?required=${true}
                name="authorizationFlow"
            >
                <select class="pf-c-form-control">
                    ${until(
                        new FlowsApi(DEFAULT_CONFIG)
                            .flowsInstancesList({
                                ordering: "pk",
                                designation: FlowsInstancesListDesignationEnum.Authentication,
                            })
                            .then((flows) => {
                                return flows.results.map((flow) => {
                                    return html`<option
                                        value=${ifDefined(flow.pk)}
                                        ?selected=${this.instance?.authorizationFlow === flow.pk}
                                    >
                                        ${flow.name} (${flow.slug})
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Flow used for users to authenticate. Currently only identification and password stages are supported.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Shared secret`}
                ?required=${true}
                name="sharedSecret"
            >
                <input
                    type="text"
                    value="${first(this.instance?.sharedSecret, randomString(128))}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Client Networks`}
                        ?required=${true}
                        name="clientNetworks"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.clientNetworks, "0.0.0.0/0")}"
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
