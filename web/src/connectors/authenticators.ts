import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { AuthenticatorsApi, Device } from "@goauthentik/api";

enum DeviceType {
    Duo = "authentik_stages_authenticator_duo.duodevice",
    SMS = "authentik_stages_authenticator_sms.smsdevice",
    TOTP = "authentik_stages_authenticator_totp.totpdevice",
    Static = "authentik_stages_authenticator_static.staticdevice",
    WebAuthn = "authentik_stages_authenticator_webauthn.webauthndevice",
    Mobile = "authentik_stages_authenticator_mobile.mobiledevice",
}

const api = () => new AuthenticatorsApi(DEFAULT_CONFIG);

// prettier-ignore
function exhaustiveGuard(_value: string): never {
    throw new Error(
        `Authenticator Device List encountered unknown device type: ${JSON.stringify(_value, null, 2,)}`
    );
}

export const retrieveAuthenticatorsAllList = () => api().authenticatorsAllList();

export const retrieveAuthenticatorsAdminAllList = (user: number) =>
    api().authenticatorsAdminAllList({ user });

export async function destroyAuthenticatorDevice(deviceType: string, id: number | string) {
    deviceType = deviceType.toLowerCase();
    const uuid = id;
    id = typeof id === "string" ? parseInt(id, 10) : id;

    switch (deviceType) {
        case DeviceType.Duo:
            return api().authenticatorsDuoDestroy({ id });
        case DeviceType.SMS:
            return api().authenticatorsSmsDestroy({ id });
        case DeviceType.TOTP:
            return api().authenticatorsTotpDestroy({ id });
        case DeviceType.Static:
            return api().authenticatorsStaticDestroy({ id });
        case DeviceType.WebAuthn:
            return api().authenticatorsWebauthnDestroy({ id });
        case DeviceType.Mobile: {
            if (typeof uuid !== "string") {
                throw new Error(`authenticatorMobile expects full UUID, received ${uuid}`);
            }
            return api().authenticatorsMobileDestroy({ uuid });
        }
        default:
            return exhaustiveGuard(deviceType);
    }
}

export async function updateAuthenticatorDevice(
    deviceType: string,
    id: number | string,
    device: Device,
) {
    deviceType = deviceType.toLowerCase();
    const uuid = id;
    id = typeof id === "string" ? parseInt(id, 10) : id;

    switch (deviceType) {
        case DeviceType.Duo:
            return api().authenticatorsDuoUpdate({ id, duoDeviceRequest: device });
        case DeviceType.SMS:
            return api().authenticatorsSmsUpdate({ id, sMSDeviceRequest: device });
        case DeviceType.TOTP:
            return api().authenticatorsTotpUpdate({ id, tOTPDeviceRequest: device });
        case DeviceType.Static:
            return api().authenticatorsStaticUpdate({ id, staticDeviceRequest: device });
        case DeviceType.WebAuthn:
            return api().authenticatorsWebauthnUpdate({ id, webAuthnDeviceRequest: device });
        case DeviceType.Mobile: {
            if (typeof uuid !== "string") {
                throw new Error(`authenticatorMobile expects full UUID, received ${uuid}`);
            }
            return api().authenticatorsMobileUpdate({ uuid, mobileDeviceRequest: device });
        }
        default:
            return exhaustiveGuard(deviceType);
    }
}
