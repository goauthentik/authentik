import { Challenge } from "authentik-api";
import {customElement, property} from "lit-element";
import {html, TemplateResult} from "lit-html";
import { PFSize } from "../../../elements/Spinner";
import { BaseStage } from "../../stages/base";
import {PlexAPIClient, popupCenterScreen} from "./API";
import {DEFAULT_CONFIG} from "../../../api/Config";
import { SourcesApi } from "authentik-api";

export interface PlexAuthenticationChallenge extends Challenge {

    client_id: string;
    slug: string;

}

@customElement("ak-flow-sources-plex")
export class PlexLoginInit extends BaseStage {

    @property({ attribute: false })
    challenge?: PlexAuthenticationChallenge;

    async firstUpdated(): Promise<void> {
        const authInfo = await PlexAPIClient.getPin(this.challenge?.client_id || "");
        const authWindow = popupCenterScreen(authInfo.authUrl, "plex auth", 550, 700);
        PlexAPIClient.pinPoll(this.challenge?.client_id || "", authInfo.pin.id).then(token => {
            authWindow?.close();
            new SourcesApi(DEFAULT_CONFIG).sourcesPlexRedeemToken({
                data: {
                    plexToken: token,
                },
                slug: this.challenge?.slug || "",
            }).then(r => {
                window.location.assign(r.to);
            });
        });
    }

    renderLoading(): TemplateResult {
        return html`<div class="ak-loading">
            <ak-spinner size=${PFSize.XLarge}></ak-spinner>
        </div>`;
    }

}
