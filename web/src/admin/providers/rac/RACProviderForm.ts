import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-tenanted-flow-search";
import { first } from "@goauthentik/app/common/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    ProtocolEnum,
    ProvidersApi,
    RACProvider,
} from "@goauthentik/api";

@customElement("ak-provider-rac-form")
export class RACProviderFormPage extends ModelForm<RACProvider, number> {
    async loadInstance(pk: number): Promise<RACProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersRacRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated provider.");
        } else {
            return msg("Successfully created provider.");
        }
    }

    async send(data: RACProvider): Promise<RACProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersRacUpdate({
                id: this.instance.pk || 0,
                rACProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersRacCreate({
                rACProviderRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                name="authorizationFlow"
                label=${msg("Authorization flow")}
                ?required=${true}
            >
                <ak-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authorization}
                    .currentFlow=${this.instance?.authorizationFlow}
                    required
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when authorizing this provider.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="host"
                        label=${msg("Host")}
                        value="${first(this.instance?.host, "")}"
                        required
                    >
                    </ak-text-input>
                    <ak-radio-input
                        name="protocol"
                        label=${msg("Client type")}
                        .value=${this.instance?.protocol}
                        required
                        .options=${[
                            {
                                label: msg("RDP"),
                                value: ProtocolEnum.Rdp,
                                default: true,
                            },
                            {
                                label: msg("SSH"),
                                value: ProtocolEnum.Ssh,
                            },
                            {
                                label: msg("VNC"),
                                value: ProtocolEnum.Vnc,
                            },
                        ]}
                    >
                    </ak-radio-input>
                    <ak-form-element-horizontal label=${msg("Settings")} name="settings">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(first(this.instance?.settings, {}))}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">${msg("Connection settings.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}
