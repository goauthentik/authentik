import { shouldResetSelectedChallenge } from "#flow/stages/authenticator_validate/challenge-selection";

import { type DeviceChallenge, DeviceClassesEnum } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

const makeDeviceChallenge = (
    deviceClass: DeviceClassesEnum,
    deviceUid: string,
): DeviceChallenge => ({
    deviceClass,
    deviceUid,
    challenge: {},
    lastUsed: null,
});

describe("shouldResetSelectedChallenge", () => {
    it("returns true when the previously selected challenge is no longer allowed", () => {
        const selected = makeDeviceChallenge(DeviceClassesEnum.Email, "email-1");
        const allowed = [
            makeDeviceChallenge(DeviceClassesEnum.Totp, "totp-1"),
            makeDeviceChallenge(DeviceClassesEnum.Webauthn, "webauthn-1"),
        ];

        expect(shouldResetSelectedChallenge(selected, allowed)).toBe(true);
    });

    it("returns false when the previously selected challenge is still allowed", () => {
        const selected = makeDeviceChallenge(DeviceClassesEnum.Email, "email-1");
        const allowed = [
            makeDeviceChallenge(DeviceClassesEnum.Email, "email-1"),
            makeDeviceChallenge(DeviceClassesEnum.Sms, "sms-1"),
        ];

        expect(shouldResetSelectedChallenge(selected, allowed)).toBe(false);
    });

    it("returns false when there was no selected challenge", () => {
        const allowed = [makeDeviceChallenge(DeviceClassesEnum.Email, "email-1")];

        expect(shouldResetSelectedChallenge(null, allowed)).toBe(false);
    });
});
