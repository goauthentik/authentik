import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { PlexAPIClient, popupCenterScreen } from "@goauthentik/common/helpers/plex";
import { MessageLevel } from "@goauthentik/common/messages";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest,
    ResponseError,
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
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle];
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
                .then((r) => {
                    window.location.assign(r.to);
                })
                .catch((r: ResponseError) => {
                    r.response.json().then((body: { detail: string }) => {
                        showMessage({
                            level: MessageLevel.error,
                            message: body.detail,
                        });
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
                    <ak-empty-state
                        ?loading="${true}"
                        header=${msg("Waiting for authentication...")}
                    >
                    </ak-empty-state>
                    <hr />
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
