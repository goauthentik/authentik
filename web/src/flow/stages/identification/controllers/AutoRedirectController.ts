import { AKFlowUpdateChallengeRequest } from "#flow/events";
import { readPendingSignIn } from "#flow/sources/plex/storage";
import type { IdentificationHost } from "#flow/stages/identification/IdentificationStage";

import { LoginSource } from "@goauthentik/api";

import { ReactiveController } from "lit";

/**
 * The source whose sign-in left for an external site and is now back.
 *
 * Source buttons swap in their stage client-side, so the server still has the
 * flow on identification. When the external site returns the browser to the
 * flow URL, this stage is what renders, and it has to hand the browser back to
 * the source that started the round trip.
 */
function findReturningSource(sources: LoginSource[]): LoginSource | null {
    const pending = readPendingSignIn();

    if (!pending) return null;

    return (
        sources.find(
            ({ challenge }) =>
                challenge.component === "ak-source-plex" && challenge.slug === pending.slug,
        ) ?? null
    );
}

/**
 * Handle automatic redirection when conditions require it
 *
 * @remarks
 *
 *   This controller contains business logic that triggers an automatic redirect to a different
 *   challenge before the host updates, if certain conditions from the first challenge are strictly
 *   met.
 */
export class AutoRedirect implements ReactiveController {
    constructor(private host: IdentificationHost) {}

    public hostUpdate() {
        const { challenge } = this.host;

        if (!challenge) {
            return;
        }

        const { userFields, passwordlessUrl, sources = [] } = challenge;

        const returningSource = findReturningSource(sources);

        if (returningSource) {
            this.host.dispatchEvent(new AKFlowUpdateChallengeRequest(returningSource.challenge));

            return;
        }

        // The rules for auto-redirect to a sole source:
        const onlyOneSource = sources.length === 1;
        const noUserAccessibleInputs = (userFields || []).length === 0;
        const noAlternativeMethods = !passwordlessUrl;

        if (onlyOneSource && noUserAccessibleInputs && noAlternativeMethods) {
            this.host.dispatchEvent(new AKFlowUpdateChallengeRequest(sources[0].challenge));
        }
    }
}

export default AutoRedirect;
