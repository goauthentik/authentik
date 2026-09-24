import {
    findMatchingChallenge,
    requiresSelectionNotification,
    shouldResetSelectedChallenge,
} from "#flow/stages/authenticator_validate/challenge-selection";

import { type DeviceChallenge, DeviceClassesEnum } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

const makeDeviceChallenge = (
    deviceClass: DeviceClassesEnum,
    deviceUid: string,
    challenge: Record<string, unknown> = {},
): DeviceChallenge => ({
    deviceClass,
    deviceUid,
    challenge,
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

describe("findMatchingChallenge", () => {
    it("returns the challenge from the new list when the selected device is still allowed", () => {
        const selected = makeDeviceChallenge(DeviceClassesEnum.Webauthn, "webauthn-1", {
            challenge: "old-nonce",
        });

        const updated = makeDeviceChallenge(DeviceClassesEnum.Webauthn, "webauthn-1", {
            challenge: "new-nonce",
        });

        const allowed = [makeDeviceChallenge(DeviceClassesEnum.Totp, "totp-1"), updated];

        expect(findMatchingChallenge(selected, allowed)).toBe(updated);
    });

    it("returns null when the selected device is no longer allowed", () => {
        const selected = makeDeviceChallenge(DeviceClassesEnum.Webauthn, "webauthn-1");
        const allowed = [makeDeviceChallenge(DeviceClassesEnum.Webauthn, "webauthn-2")];

        expect(findMatchingChallenge(selected, allowed)).toBeNull();
    });

    it("returns null when there was no selected challenge", () => {
        const allowed = [makeDeviceChallenge(DeviceClassesEnum.Webauthn, "webauthn-1")];

        expect(findMatchingChallenge(null, allowed)).toBeNull();
    });
});

describe("requiresSelectionNotification", () => {
    it.each([DeviceClassesEnum.Sms, DeviceClassesEnum.Email])(
        "returns true when selecting a %s challenge sends a code",
        (deviceClass) => {
            expect(requiresSelectionNotification(makeDeviceChallenge(deviceClass, "1"))).toBe(true);
        },
    );

    it.each([
        DeviceClassesEnum.Webauthn,
        DeviceClassesEnum.Totp,
        DeviceClassesEnum.Static,
        DeviceClassesEnum.Duo,
    ])("returns false when selecting a %s challenge has no backend effect", (deviceClass) => {
        expect(requiresSelectionNotification(makeDeviceChallenge(deviceClass, "1"))).toBe(false);
    });

    it("returns false when there was no selected challenge", () => {
        expect(requiresSelectionNotification(null)).toBe(false);
    });
});
