import { type DeviceChallenge, DeviceClassesEnum } from "@goauthentik/api";

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

/**
 * Whether the backend has to be told which challenge was selected before the user can answer it.
 *
 * Only SMS and email need this, as selecting them sends the code to the user. For every other
 * device class, the notification has no effect on the backend, but it's a flow executor request
 * that persists the session, so racing it against the actual challenge response can overwrite
 * the flow progress made by that response.
 */
export function requiresSelectionNotification(challenge: DeviceChallenge | null): boolean {
    if (!challenge) {
        return false;
    }

    return (
        challenge.deviceClass === DeviceClassesEnum.Sms ||
        challenge.deviceClass === DeviceClassesEnum.Email
    );
}
