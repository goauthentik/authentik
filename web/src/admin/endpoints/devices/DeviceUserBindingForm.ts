import "#components/ak-switch-input";

import { aki } from "#common/api/client";
import { PolicyBindingCheckTarget } from "#common/policies/utils";

import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";

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
        if (binding?.policyObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.Policy;
        }
        if (binding?.groupObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.Group;
        }
        if (binding?.userObj) {
            this.policyGroupUser = PolicyBindingCheckTarget.User;
        }
        this.defaultOrder = await this.getOrder();
        return binding;
    }

    async send(data: PolicyBinding): Promise<unknown> {
        if (this.targetPk) {
            data.target = this.targetPk;
        }
        switch (this.policyGroupUser) {
            case PolicyBindingCheckTarget.Policy:
                data.user = null;
                data.group = null;
                break;
            case PolicyBindingCheckTarget.Group:
                data.policy = null;
                data.user = null;
                break;
            case PolicyBindingCheckTarget.User:
                data.policy = null;
                data.group = null;
                break;
        }

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
