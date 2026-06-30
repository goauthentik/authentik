import "#components/ak-switch-input";

import { aki } from "#common/api/client";

import {
    cleanBindingForSend,
    pickPolicyGroupUser,
    PolicyBindingForm,
} from "#admin/policies/PolicyBindingForm";

import { DeviceUserBinding, EndpointsApi, PolicyBinding } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-device-binding-form")
export class DeviceUserBindingForm extends PolicyBindingForm<DeviceUserBinding> {
    async loadInstance(pk: string): Promise<DeviceUserBinding> {
        const binding = await aki(EndpointsApi).endpointsDeviceBindingsRetrieve({
            policyBindingUuid: pk,
        });
        this.policyGroupUser = pickPolicyGroupUser(binding, this.policyGroupUser);
        this.defaultOrder = await this.getOrder();

        return binding;
    }

    async send(data: PolicyBinding): Promise<unknown> {
        if (this.targetPk) {
            data.target = this.targetPk;
        }

        data = cleanBindingForSend(data, this.policyGroupUser);

        if (this.instance?.pk) {
            return aki(EndpointsApi).endpointsDeviceBindingsUpdate({
                policyBindingUuid: this.instance.pk,
                deviceUserBindingRequest: data,
            });
        }

        return aki(EndpointsApi).endpointsDeviceBindingsCreate({
            deviceUserBindingRequest: data,
        });
    }

    public override renderForm() {
        return html`<ak-switch-input
                name="isPrimary"
                label=${msg("Is Primary user")}
                ?checked=${this.instance?.isPrimary ?? false}
            >
            </ak-switch-input>

            ${super.renderForm()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-device-binding-form": DeviceUserBindingForm;
    }
}
