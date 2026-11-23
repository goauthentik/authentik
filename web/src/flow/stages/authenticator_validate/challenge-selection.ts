import { type DeviceChallenge, DeviceClassesEnum } from "@goauthentik/api";

export function shouldResetSelectedChallenge(
    selectedChallenge: DeviceChallenge | null,
    allowedChallenges: DeviceChallenge[],
): boolean {
    if (!selectedChallenge) {
        return false;
    }

    return !allowedChallenges.some(
        (challenge) =>
            challenge.deviceClass === selectedChallenge.deviceClass &&
            challenge.deviceUid === selectedChallenge.deviceUid,
    );
}

/**
 * Whether selecting this challenge has an effect on the server.
 *
 * Only SMS and email do, as selecting them sends a code.
 */
export function requiresSelectionNotification(challenge: DeviceChallenge): boolean {
    return (
        challenge.deviceClass === DeviceClassesEnum.Sms ||
        challenge.deviceClass === DeviceClassesEnum.Email
    );
}
