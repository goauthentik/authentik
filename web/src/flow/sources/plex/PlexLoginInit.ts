import "#elements/EmptyState";
import "#flow/components/ak-flow-card";

import { DEFAULT_CONFIG } from "#common/api/config";
import { parseAPIResponseError } from "#common/errors/network";
import { PlexAPIClient, popupCenterScreen } from "#common/helpers/plex";

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
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-flow-source-plex")
export class PlexLoginInit extends BaseStage<
    PlexAuthenticationChallenge,
    PlexAuthenticationChallengeResponseRequest
> {
    @state()
    authUrl?: string;

    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFButton, PFTitle, PFDivider];

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
        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Authenticating with Plex...")}</span>
            <form class="pf-c-form">
                <ak-empty-state loading
                    ><span>${msg("Waiting for authentication...")}></span>
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
        </ak-flow-card>`;
    }
}

export default PlexLoginInit;

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-source-plex": PlexLoginInit;
    }
}
