import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { PlexAPIClient, popupCenterScreen } from "@goauthentik/web/api/Plex";
import { MessageLevel } from "@goauthentik/web/elements/messages/Message";
import { showMessage } from "@goauthentik/web/elements/messages/MessageContainer";
import { BaseStage } from "@goauthentik/web/flows/stages/base";

import { t } from "@lingui/macro";

import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
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

@customElement("ak-flow-sources-plex")
export class PlexLoginInit extends BaseStage<
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle, AKGlobal];
    }

    async firstUpdated(): Promise<void> {
        const authInfo = await PlexAPIClient.getPin(this.challenge?.clientId || "");
        const authWindow = popupCenterScreen(authInfo.authUrl, "plex auth", 550, 700);
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
                <h1 class="pf-c-title pf-m-3xl">${t`Authenticating with Plex...`}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <ak-empty-state ?loading="${true}"> </ak-empty-state>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
