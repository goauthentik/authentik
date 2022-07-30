import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { PlexAPIClient, popupCenterScreen } from "@goauthentik/web/api/Plex";
import { EVENT_REFRESH } from "@goauthentik/web/constants";
import { MessageLevel } from "@goauthentik/web/elements/messages/Message";
import { showMessage } from "@goauthentik/web/elements/messages/MessageContainer";
import { BaseUserSettings } from "@goauthentik/web/user/user-settings/BaseUserSettings";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import { SourcesApi } from "@goauthentik/api";

@customElement("ak-user-settings-source-plex")
export class SourceSettingsPlex extends BaseUserSettings {
    @property()
    title!: string;

    async doPlex(): Promise<void> {
        const authInfo = await PlexAPIClient.getPin(this.configureUrl || "");
        const authWindow = popupCenterScreen(authInfo.authUrl, "plex auth", 550, 700);
        PlexAPIClient.pinPoll(this.configureUrl || "", authInfo.pin.id).then((token) => {
            authWindow?.close();
            new SourcesApi(DEFAULT_CONFIG).sourcesPlexRedeemTokenAuthenticatedCreate({
                plexTokenRedeemRequest: {
                    plexToken: token,
                },
                slug: this.objectId,
            });
        });
        this.dispatchEvent(
            new CustomEvent(EVENT_REFRESH, {
                bubbles: true,
                composed: true,
            }),
        );
    }

    render(): TemplateResult {
        return html`${until(
            new SourcesApi(DEFAULT_CONFIG)
                .sourcesUserConnectionsPlexList({
                    sourceSlug: this.objectId,
                })
                .then((connection) => {
                    if (connection.results.length > 0) {
                        return html` <button
                            class="pf-c-button pf-m-danger"
                            @click=${() => {
                                return new SourcesApi(DEFAULT_CONFIG)
                                    .sourcesUserConnectionsPlexDestroy({
                                        id: connection.results[0].pk || 0,
                                    })
                                    .then(() => {
                                        showMessage({
                                            level: MessageLevel.info,
                                            message: t`Successfully disconnected source`,
                                        });
                                    })
                                    .catch((exc) => {
                                        showMessage({
                                            level: MessageLevel.error,
                                            message: t`Failed to disconnected source: ${exc}`,
                                        });
                                    });
                            }}
                        >
                            ${t`Disconnect`}
                        </button>`;
                    }
                    return html` <button @click=${this.doPlex} class="pf-c-button pf-m-primary">
                        ${t`Connect`}
                    </button>`;
                }),
        )}`;
    }
}
