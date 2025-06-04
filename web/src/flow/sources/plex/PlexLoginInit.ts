import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { parseAPIResponseError } from "@goauthentik/common/errors/network";
import { PlexAPIClient, popupCenterScreen } from "@goauthentik/common/helpers/plex";
import { showAPIErrorMessage } from "@goauthentik/elements/messages/MessageContainer";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest,
} from "@goauthentik/api";
import { SourcesApi } from "@goauthentik/api";

@customElement("ak-flow-source-plex")
export class PlexLoginInit extends BaseStage<
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest
> {
    @state()
    authUrl?: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle, PFDivider];
    }

    async firstUpdated(): Promise<void> {
        const authInfo = await PlexAPIClient.getPin(this.challenge?.clientId || "");
        this.authUrl = authInfo.authUrl;
        const authWindow = await popupCenterScreen(authInfo.authUrl, "plex auth", 550, 700);
        PlexAPIClient.pinPoll(this.challenge?.clientId || "", authInfo.pin.id).then((token) => {
            authWindow?.close();
            new SourcesApi(DEFAULT_CONFIG)
                .sourcesPlexRedeemTokenCreate({
                    plexTokenRedeemRequest: {
                        plexToken: token,
                    },
                    slug: this.challenge?.slug || "",
                })
                .then((redirectChallenge) => {
                    window.location.assign(redirectChallenge.to);
                })
                .catch(async (error: unknown) => {
                    return parseAPIResponseError(error)
                        .then(showAPIErrorMessage)
                        .then(() => {
                            setTimeout(() => {
                                window.location.assign("/");
                            }, 5000);
                        });
                });
        });
    }

    render(): TemplateResult {
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${msg("Authenticating with Plex...")}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <ak-empty-state loading header=${msg("Waiting for authentication...")}>
                    </ak-empty-state>
                    <hr class="pf-c-divider" />
                    <p>${msg("If no Plex popup opens, click the button below.")}</p>
                    <button
                        class="pf-c-button pf-m-block pf-m-primary"
                        type="button"
                        @click=${() => {
                            window.open(this.authUrl, "_blank");
                        }}
                    >
                        ${msg("Open login")}
                    </button>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-source-plex": PlexLoginInit;
    }
}
