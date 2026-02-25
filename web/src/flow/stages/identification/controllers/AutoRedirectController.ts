import { AKFlowUpdateChallengeRequest } from "#flow/events";
import type { IdentificationHost } from "#flow/stages/identification/IdentificationStage";

import { ReactiveController } from "lit";

export class AutoRedirect implements ReactiveController {
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

        if (onlyOneSource && noUserAccessibleInputs && noAlternativeMethods) {
            this.host.dispatchEvent(new AKFlowUpdateChallengeRequest(sources[0].challenge));
        }
    }
}

export default AutoRedirect;
