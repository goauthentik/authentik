import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";
import { PolicyBindingCheckTarget } from "#admin/policies/utils";

import { DeviceUserBinding, EndpointsApi, PolicyBinding } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-device-binding-form")
export class DeviceUserBindingForm extends PolicyBindingForm<DeviceUserBinding> {
    async loadInstance(pk: string): Promise<DeviceUserBinding> {
        const binding = await new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceBindingsRetrieve({
            policyBindingUuid: pk,
        });
        if (binding?.policyObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.policy;
        }
        if (binding?.groupObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.group;
        }
        if (binding?.userObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.user;
        }
        this.defaultOrder = await this.getOrder();
        return binding;
    }

    async send(data: PolicyBinding): Promise<unknown> {
        if (this.targetPk) {
            data.target = this.targetPk;
        }
        switch (this.policyGroupUser) {
            case PolicyBindingCheckTarget.policy:
                data.user = null;
                data.group = null;
                break;
            case PolicyBindingCheckTarget.group:
                data.policy = null;
                data.user = null;
                break;
            case PolicyBindingCheckTarget.user:
                data.policy = null;
                data.group = null;
                break;
        }

        if (this.instance?.pk) {
            return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceBindingsUpdate({
                policyBindingUuid: this.instance.pk,
                deviceUserBindingRequest: data,
            });
        }
        return new EndpointsApi(DEFAULT_CONFIG).endpointsDeviceBindingsCreate({
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
