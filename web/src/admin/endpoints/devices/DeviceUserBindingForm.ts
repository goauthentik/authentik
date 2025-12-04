import { DEFAULT_CONFIG } from "#common/api/config";

import { PolicyBindingForm } from "#admin/policies/PolicyBindingForm";
import { PolicyBindingCheckTarget } from "#admin/policies/utils";

import { DeviceUserBinding, EndpointsApi } from "@goauthentik/api";

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

    renderForm() {
        return html`<ak-form-element-horizontal name="isPrimary">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.isPrimary ?? false}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Is Primary user")}</span>
                </label> </ak-form-element-horizontal
            >${super.renderForm()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-device-binding-form": DeviceUserBindingForm;
    }
}
