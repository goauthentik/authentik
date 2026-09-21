import { type DeviceChallenge } from "@goauthentik/api";

/**
 * Find the entry in a freshly received list of device challenges that refers to the same
 * device as the currently selected challenge.
 *
 * The backend can return updated challenge data for a later authentication attempt, so the
 * selected object must be swapped for its counterpart from the latest response rather than kept
 * around. Otherwise, the client can keep answering challenge data the server no longer accepts.
 */
export function findMatchingChallenge(
    selectedChallenge: DeviceChallenge | null,
    allowedChallenges: DeviceChallenge[],
): DeviceChallenge | null {
    if (!selectedChallenge) {
        return null;
    }

    return (
        allowedChallenges.find(
            (challenge) =>
                challenge.deviceClass === selectedChallenge.deviceClass &&
                challenge.deviceUid === selectedChallenge.deviceUid,
        ) ?? null
    );
}

export function shouldResetSelectedChallenge(
    selectedChallenge: DeviceChallenge | null,
    allowedChallenges: DeviceChallenge[],
): boolean {
    if (!selectedChallenge) {
        return false;
    }

    return !findMatchingChallenge(selectedChallenge, allowedChallenges);
}
