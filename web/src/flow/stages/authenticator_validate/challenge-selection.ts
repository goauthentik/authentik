import { type DeviceChallenge } from "@goauthentik/api";

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
