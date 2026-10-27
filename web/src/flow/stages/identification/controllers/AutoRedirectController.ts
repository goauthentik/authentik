import { AKFlowUpdateChallengeRequest } from "#flow/events";
import type { IdentificationHost } from "#flow/stages/identification/IdentificationStage";
import { multiTabClaimSignIn, multiTabCoordinationEnabled } from "#flow/tabs/orchestrator";

import { IdentificationChallenge } from "@goauthentik/api";

import { ReactiveController } from "lit";

/**
 * Handle automatic redirection when conditions require it
 *
 * @remarks
 *
 *   This controller contains business logic that triggers an automatic redirect to a different
 *   challenge before the host updates, if certain conditions from the first challenge are strictly
 *   met.
 *   With continuous login enabled, only one tab redirects at a time. The others stay on this stage
 *   until the redirecting tab signs in and resumes them.
 */
export class AutoRedirect implements ReactiveController {
    #claimedChallenge: IdentificationChallenge | null = null;

    constructor(private host: IdentificationHost) {}

    public hostUpdate() {
        const { challenge } = this.host;

        if (!challenge) {
            return;
        }

        const { userFields, passwordlessUrl, sources = [] } = challenge;

        // The rules for auto-redirect:
        const onlyOneSource = sources.length === 1;
        const noUserAccessibleInputs = (userFields || []).length === 0;
        const noAlternativeMethods = !passwordlessUrl;

        if (!onlyOneSource || !noUserAccessibleInputs || !noAlternativeMethods) {
            return;
        }

        const redirect = () => {
            this.host.dispatchEvent(new AKFlowUpdateChallengeRequest(sources[0].challenge));
        };

        if (!multiTabCoordinationEnabled()) {
            redirect();

            return;
        }

        if (this.#claimedChallenge === challenge) {
            return;
        }

        this.#claimedChallenge = challenge;

        multiTabClaimSignIn().then((claimed) => {
            if (claimed && this.host.challenge === challenge) {
                redirect();
            }
        });
    }
}

export default AutoRedirect;
