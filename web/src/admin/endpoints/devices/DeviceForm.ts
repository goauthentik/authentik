import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import "#elements/utils/TimeDeltaHelp";
import "#admin/endpoints/ak-endpoints-device-group-search";
import "#elements/CodeMirror";

import { DEFAULT_CONFIG } from "#common/api/config";

import { CodeMirrorMode } from "#elements/CodeMirror";
import { ModelForm } from "#elements/forms/ModelForm";

import { EndpointDevice, EndpointsApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-device-form")
export class EndpointDeviceForm extends ModelForm<EndpointDevice, string> {
    loadInstance(pk: string): Promise<EndpointDevice> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDevicesRetrieve({
            deviceUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return msg("Successfully updated device.");
    }

    async send(data: EndpointDevice): Promise<EndpointDevice> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDevicesPartialUpdate({
            deviceUuid: this.instance!.deviceUuid!,
            patchedEndpointDeviceRequest: data,
        });
    }

    renderForm() {
        return html`<ak-text-input
                name="name"
                placeholder=${msg("Device name...")}
                label=${msg("Device name")}
                value=${ifDefined(this.instance?.name)}
                required
            ></ak-text-input>
            <ak-form-element-horizontal label=${msg("Device Group")} name="group">
                <ak-endpoints-device-group-search
                    .group=${this.instance?.group}
                ></ak-endpoints-device-group-search>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Attributes")} name="attributes">
                <ak-codemirror
                    mode=${CodeMirrorMode.YAML}
                    value="${YAML.stringify(this.instance?.attributes ?? {})}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-device-form": EndpointDeviceForm;
    }
}
