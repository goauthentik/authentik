import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { AuthModeEnum, Endpoint, ProtocolEnum, RacApi } from "@goauthentik/api";

@customElement("ak-rac-endpoint-form")
export class EndpointForm extends ModelForm<Endpoint, string> {
    @property({ type: Number })
    providerID?: number;

    loadInstance(pk: string): Promise<Endpoint> {
        return new RacApi(DEFAULT_CONFIG).racEndpointsRetrieve({
            pbmUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated endpoint.")
            : msg("Successfully created endpoint.");
    }

    async send(data: Endpoint): Promise<Endpoint> {
        data.authMode = AuthModeEnum.Prompt;
        data.provider = this.providerID || 0;
        if (this.instance) {
            return new RacApi(DEFAULT_CONFIG).racEndpointsPartialUpdate({
                pbmUuid: this.instance.pk || "",
                patchedEndpointRequest: data,
            });
        } else {
            return new RacApi(DEFAULT_CONFIG).racEndpointsCreate({
                endpointRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Name")} name="name" ?required=${true}>
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Protocol")} ?required=${true} name="protocol">
                <ak-radio
                    .options=${[
                        {
                            label: msg("RDP"),
                            value: ProtocolEnum.Rdp,
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
                    .value=${this.instance?.protocol}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Host")} name="host" ?required=${true}>
                <input
                    type="text"
                    value="${ifDefined(this.instance?.host)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${msg("Hostname/IP to connect to.")}</p>
            </ak-form-element-horizontal>
        `;
    }
}
