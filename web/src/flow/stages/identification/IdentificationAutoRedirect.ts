import "#flow/stages/captcha/CaptchaStage";

import type { IdentificationHost } from "./IdentificationStage";

import { ReactiveController } from "lit";

export class IdentificationAutoRedirect implements ReactiveController {
    constructor(private host: IdentificationHost) {}

    public hostUpdate() {
        const { challenge } = this.host;
        if (!challenge) {
            return;
        }

        const { userFields, passwordlessUrl, sources = [] } = challenge;

        // We only want to auto-redirect when:
        // - There's only one source (No alternative to the destination)
        // - There are no user fields to select (No alternatives!)
        // - Passwordless is not configured (No alternatives!!)
        if (sources.length !== 1 || (userFields || []).length !== 0 || passwordlessUrl) {
            return;
        }

        this.host.host.challenge = sources[0].challenge;
    }
}
