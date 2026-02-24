import "#flow/stages/captcha/CaptchaStage";

import type { IdentificationHost } from "./IdentificationStage";

import { AKFlowUpdateChallengeRequest } from "#flow/events";

import { ReactiveController } from "lit";

export class IdentificationAutoRedirect implements ReactiveController {
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
