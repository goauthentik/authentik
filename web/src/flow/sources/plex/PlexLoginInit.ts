import "#elements/EmptyState";
import "#flow/components/ak-flow-card";
import "#elements/Divider";

import { aki } from "#common/api/client";
import { PlexAPIClient } from "#common/helpers/plex";

import { showAPIErrorMessage } from "#elements/messages/MessageContainer";

import { BaseStage } from "#flow/stages/base";

import {
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest,
    SourcesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

// State for the round trip to app.plex.tv rides in the flow URL itself (via
// Plex's forwardUrl) rather than in web storage: Safari partitions storage in
// private browsing, so a stored pin would not survive the cross-origin hop.
const PLEX_PIN_PARAM = "plex_pin";
const PLEX_ATTEMPT_PARAM = "plex_attempt";
// After this many automatic round trips without a token, stop redirecting so a
// broken return path cannot loop, and leave the manual button as the way in.
const MAX_REDIRECT_ATTEMPTS = 2;
// How long the return leg waits for plex.tv to report the pin as authorized.
const RETURN_POLL_TIMEOUT = 20 * 1000;

@customElement("ak-flow-source-plex")
export class PlexLoginInit extends BaseStage<
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest
> {
    @state()
    authUrl?: string;

    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFButton, PFTitle];

    async firstUpdated(): Promise<void> {
        const clientId = this.challenge?.clientId || "";
        const currentParams = new URLSearchParams(window.location.search);
        const returnedPin = parseInt(currentParams.get(PLEX_PIN_PARAM) || "", 10);
        const attempt = parseInt(currentParams.get(PLEX_ATTEMPT_PARAM) || "", 10) || 0;

        // Return leg: Plex sent the browser back here through forwardUrl.
        if (!Number.isNaN(returnedPin)) {
            let token: string | undefined;
            try {
                token = await PlexAPIClient.pinPoll(clientId, returnedPin, RETURN_POLL_TIMEOUT);
            } catch {
                // The pin expired or was never authorized: fall through and
                // mint a fresh one, bounded by the attempt counter.
            }
            if (token) {
                try {
                    const redirectChallenge = await aki(SourcesApi).sourcesPlexRedeemTokenCreate({
                        plexTokenRedeemRequest: {
                            plexToken: token,
                        },
                        slug: this.challenge?.slug || "",
                    });
                    window.location.assign(redirectChallenge.to);
                    return;
                } catch (error: unknown) {
                    await showAPIErrorMessage(error);
                    return;
                }
            }
        }

        const authInfo = await PlexAPIClient.getPin(clientId);
        // The return URL keeps the flow's whole query string: dropping `next`
        // would complete the flow but lose the final hop back to the
        // application that started it.
        const returnParams = new URLSearchParams(window.location.search);
        returnParams.set(PLEX_PIN_PARAM, authInfo.pin.id.toString());
        returnParams.set(PLEX_ATTEMPT_PARAM, (attempt + 1).toString());
        const returnUrl = `${window.location.origin}${window.location.pathname}?${returnParams.toString()}`;
        this.authUrl = PlexAPIClient.authUrl(clientId, authInfo.pin.code, returnUrl);
        if (attempt >= MAX_REDIRECT_ATTEMPTS) {
            return;
        }
        // replace, not assign: keeps the pre-redirect flow URL out of history,
        // so the Back button on plex.tv does not land on a page that would
        // immediately redirect there again.
        window.location.replace(this.authUrl);
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Authenticating with Plex...")}</span>
            <form class="pf-c-form">
                <ak-empty-state loading
                    ><span>${msg("Waiting for authentication...")}></span>
                </ak-empty-state>
                <ak-divider></ak-divider>
                <p>${msg("If you are not redirected to Plex, click the button below.")}</p>
                <button
                    class="pf-c-button pf-m-block pf-m-primary"
                    type="button"
                    @click=${() => {
                        if (this.authUrl) {
                            window.location.assign(this.authUrl);
                        }
                    }}
                >
                    ${msg("Continue to Plex")}
                </button>
            </form>
        </ak-flow-card>`;
    }
}

export default PlexLoginInit;

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-source-plex": PlexLoginInit;
    }
}
