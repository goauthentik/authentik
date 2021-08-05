import { t } from "@lingui/macro";
import {
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest,
} from "authentik-api";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { CSSResult, customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { BaseStage } from "../../stages/base";
import { PlexAPIClient, popupCenterScreen } from "./API";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { SourcesApi } from "authentik-api";
import { showMessage } from "../../../elements/messages/MessageContainer";
import { MessageLevel } from "../../../elements/messages/Message";

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
                .catch((r: Response) => {
                    r.json().then((body: { detail: string }) => {
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
