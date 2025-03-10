import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { SentryIgnoredError } from "@goauthentik/common/errors";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { AuthenticatorsApi, Device } from "@goauthentik/api";

@customElement("ak-user-mfa-form")
export class MFADeviceForm extends ModelForm<Device, string> {
    @property()
    deviceType!: string;

    async loadInstance(pk: string): Promise<Device> {
        const devices = await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsAllList();
        return devices.filter((device) => {
            return device.pk === pk && device.type === this.deviceType;
        })[0];
    }

    getSuccessMessage(): string {
        return msg("Successfully updated device.");
    }

    async send(device: Device): Promise<Device> {
        switch (this.instance?.type) {
            case "authentik_stages_authenticator_duo.DuoDevice":
                await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsDuoUpdate({
                    id: parseInt(this.instance?.pk, 10),
                    duoDeviceRequest: device,
                });
                break;
            case "authentik_stages_authenticator_email.EmailDevice":
                await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsEmailUpdate({
                    id: parseInt(this.instance?.pk, 10),
                    emailDeviceRequest: device,
                });
                break;
            case "authentik_stages_authenticator_sms.SMSDevice":
                await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsSmsUpdate({
                    id: parseInt(this.instance?.pk, 10),
                    sMSDeviceRequest: device,
                });
                break;
            case "authentik_stages_authenticator_totp.TOTPDevice":
                await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsTotpUpdate({
                    id: parseInt(this.instance?.pk, 10),
                    tOTPDeviceRequest: device,
                });
                break;
            case "authentik_stages_authenticator_static.StaticDevice":
                await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsStaticUpdate({
                    id: parseInt(this.instance?.pk, 10),
                    staticDeviceRequest: device,
                });
                break;
            case "authentik_stages_authenticator_webauthn.WebAuthnDevice":
                await new AuthenticatorsApi(DEFAULT_CONFIG).authenticatorsWebauthnUpdate({
                    id: parseInt(this.instance?.pk, 10),
                    webAuthnDeviceRequest: device,
                });
                break;
            default:
                throw new SentryIgnoredError(
                    msg(str`Device type ${device.verboseName} cannot be edited`),
                );
        }
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-mfa-form": MFADeviceForm;
    }
}
