import {
    retrieveAuthenticatorsAllList,
    updateAuthenticatorDevice,
} from "@goauthentik/connectors/authenticators";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Device } from "@goauthentik/api";

@customElement("ak-user-mfa-form")
export class MFADeviceForm extends ModelForm<Device, string> {
    @property()
    deviceType!: string;

    async loadInstance(pk: string): Promise<Device> {
        return (await retrieveAuthenticatorsAllList()).filter((device) => {
            return device.pk === pk && device.type === this.deviceType;
        })[0];
    }

    getSuccessMessage(): string {
        return msg("Successfully updated device.");
    }

    async send(device: Device): Promise<Device> {
        if (!this.instance) {
            return device;
        }
        await updateAuthenticatorDevice(this.instance.type, this.instance.pk, device);
        return device;
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
            <input
                type="text"
                value="${ifDefined(this.instance?.name)}"
                class="pf-c-form-control"
                required
            />
        </ak-form-element-horizontal>`;
    }
}
