import "#elements/Spinner";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { PlexAPIClient, popupCenterScreen } from "#common/helpers/plex";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { BaseUserSettings } from "#elements/user/sources/BaseUserSettings";

import { SourcesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-settings-source-plex")
export class SourceSettingsPlex extends BaseUserSettings {
    protected disconnectSource(): Promise<void> {
        return new SourcesApi(DEFAULT_CONFIG)
            .sourcesUserConnectionsPlexDestroy({
                id: this.connectionPk,
            })
            .then(() => {
                showMessage({
                    level: MessageLevel.info,
                    message: msg("Successfully disconnected source"),
                });
            })
            .catch(async (error: unknown) => {
                const parsedError = await parseAPIResponseError(error);
                showMessage({
                    level: MessageLevel.error,
                    message: msg(
                        str`Failed to disconnected source: ${pluckErrorDetail(parsedError)}`,
                    ),
                });
            })
            .finally(() => {
                this.parentElement?.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );
            });
    }

    protected async authenticateWithPlex(): Promise<void> {
        const authInfo = await PlexAPIClient.getPin(this.configureURL || "");
        const authWindow = await popupCenterScreen(authInfo.authUrl, "plex auth", 550, 700);

        PlexAPIClient.pinPoll(this.configureURL || "", authInfo.pin.id).then((token) => {
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

    protected renderConnectButton(): SlottedTemplateResult {
        return html`<button @click=${this.authenticateWithPlex} class="pf-c-button pf-m-primary">
            ${msg("Connect")}
        </button>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-source-plex": SourceSettingsPlex;
    }
}
