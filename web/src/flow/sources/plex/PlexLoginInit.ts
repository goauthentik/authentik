import "#elements/EmptyState";
import "#flow/components/ak-flow-card";
import "#elements/Divider";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

import { aki } from "#common/api/client";
import { PlexAPIClient } from "#common/helpers/plex";

import { showAPIErrorMessage } from "#elements/messages/MessageContainer";

import {
    clearAttempts,
    clearPendingSignIn,
    readAttempt,
    readPendingSignIn,
    writeAttempt,
    writePendingSignIn,
} from "#flow/sources/plex/storage";
import { BaseStage } from "#flow/stages/base";

import {
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest,
    SourcesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

// After this many automatic redirects without a completed sign-in, stop
// redirecting so a broken return path cannot loop, and leave the manual
// button as the way in.
const MAX_REDIRECT_ATTEMPTS = 2;

@customElement("ak-flow-source-plex")
export class PlexLoginInit extends BaseStage<
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest
> {
    // Set when a sign-in attempt has failed; switches the card from the
    // waiting spinner to an actionable retry state.
    @state()
    errorMessage?: string;

    // Set when the automatic-redirect cap has been reached and the component
    // is deliberately not navigating on its own.
    @state()
    capped = false;

    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFButton, PFTitle];

    get clientId(): string {
        return this.challenge?.clientId || "";
    }

    async firstUpdated(): Promise<void> {
        const pending = readPendingSignIn();

        // Return leg: Plex sent the browser back to the flow through
        // forwardUrl, the identification stage handed over to this source's
        // stage, and the pin this session left with is waiting in storage.
        if (pending && pending.slug === this.challenge?.slug) {
            clearPendingSignIn();
            await this.completeReturn(pending.pin);

            return;
        }

        if (readAttempt() >= MAX_REDIRECT_ATTEMPTS) {
            this.capped = true;

            return;
        }

        try {
            await this.redirectToPlex(false);
        } catch (error: unknown) {
            await showAPIErrorMessage(error);
            this.errorMessage = msg("Could not start sign-in with Plex.");
        }
    }

    // Handle the browser coming back from app.plex.tv with a pin this
    // session started.
    private async completeReturn(pin: number): Promise<void> {
        // Getting here at all proves the return path works, so the
        // automatic-redirect budget has done its job and starts over. It only
        // exists to stop a return path that never comes back from looping, and
        // a counter that survived until the next sign-in would cap a fresh
        // attempt that has not redirected yet.
        clearAttempts();
        let token: string | undefined;

        try {
            // A single immediate status check instead of a poll: Plex only
            // follows forwardUrl once the pin is authorized, so by the time
            // the browser is back the token is either already there or the
            // user backed out without finishing.
            token = await PlexAPIClient.pinStatus(this.clientId, pin);
        } catch {
            token = undefined;
        }

        if (!token) {
            this.errorMessage = msg("Sign-in with Plex was cancelled or timed out.");

            return;
        }

        try {
            const redirectChallenge = await aki(SourcesApi).sourcesPlexRedeemTokenCreate({
                plexTokenRedeemRequest: {
                    plexToken: token,
                },
                slug: this.challenge?.slug || "",
            });

            this.navigate(redirectChallenge.to);
        } catch (error: unknown) {
            await showAPIErrorMessage(error);
            this.errorMessage = msg("Plex sign-in succeeded, but completing the login failed.");
        }
    }

    // Mint a fresh pin, persist it for the return leg, and send the browser
    // to app.plex.tv.
    private async redirectToPlex(manual: boolean): Promise<void> {
        const authInfo = await PlexAPIClient.getPin(this.clientId);
        // The return URL keeps the flow's whole query string: dropping `next`
        // would complete the flow but lose the final hop back to the
        // application that started it.
        const returnUrl = `${window.location.origin}${window.location.pathname}${window.location.search}`;
        const authUrl = PlexAPIClient.authUrl(this.clientId, authInfo.pin.code, returnUrl);

        const stored = writePendingSignIn({
            slug: this.challenge?.slug || "",
            pin: authInfo.pin.id,
        });

        if (!stored) {
            // Nothing recognizes the return leg without the stored pin, so the
            // trip to Plex could only come back to a page that starts another
            // one. Say so rather than sending the user out with no way home.
            this.errorMessage = msg(
                "Sign-in with Plex needs session storage, which this browser is blocking.",
            );

            return;
        }

        writeAttempt(readAttempt() + 1);

        // An automatic redirect replaces rather than assigns: keeps the
        // pre-redirect flow URL out of history, so the Back button on plex.tv
        // does not land on a page that would immediately redirect there again.
        this.navigate(authUrl, !manual);
    }

    // Every navigation away from the stage goes through here, so tests can
    // observe it without the browser leaving the page.
    protected navigate(url: string, replace = false): void {
        if (replace) {
            window.location.replace(url);

            return;
        }

        window.location.assign(url);
    }

    private onContinue = (): void => {
        this.errorMessage = undefined;
        this.capped = false;

        this.redirectToPlex(true).catch(async (error: unknown) => {
            await showAPIErrorMessage(error);
            this.errorMessage = msg("Could not start sign-in with Plex.");
        });
    };

    render(): TemplateResult {
        let heading = msg("Waiting for authentication...");
        let hint = msg("If you are not redirected to Plex, click the button below.");

        if (this.errorMessage) {
            heading = this.errorMessage;
            hint = msg("Click the button below to start over with a new sign-in attempt.");
        } else if (this.capped) {
            heading = msg("Not redirecting to Plex automatically.");

            hint = msg(
                "Sign-in did not complete after multiple redirects. Click the button below to continue to Plex.",
            );
        }

        const loading = !this.errorMessage && !this.capped;

        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Authenticating with Plex...")}</span>
            <form class="pf-c-form">
                ${
                    loading
                        ? html`<ak-empty-state loading><span>${heading}</span></ak-empty-state>`
                        : html`<ak-empty-state icon="fa-times"
                              ><span>${heading}</span></ak-empty-state
                          >`
                }
                <ak-divider></ak-divider>
                <p>${hint}</p>
                <button
                    class="pf-c-button pf-m-block pf-m-primary"
                    type="button"
                    @click=${this.onContinue}
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
