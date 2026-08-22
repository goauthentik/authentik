import "#elements/Spinner";

import { aki } from "#common/api/client";
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
        return aki(SourcesApi)
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
        // Opened before awaiting the pin: the click's user activation is gone by
        // the time the pin request resolves, and the popup would be blocked.
        const authWindow = popupCenterScreen("about:blank", "plex auth", 550, 700);
        const clientId = this.configureURL || "";
        const authInfo = await PlexAPIClient.getPin(clientId);
        if (authWindow && !authWindow.closed) {
            authWindow.location.replace(authInfo.authUrl);
        }

        PlexAPIClient.pinPoll(clientId, authInfo.pin.id)
            .then((token) => {
                authWindow?.close();
                aki(SourcesApi).sourcesPlexRedeemTokenAuthenticatedCreate({
                    plexTokenRedeemRequest: {
                        plexToken: token,
                    },
                    slug: this.objectId,
                });
            })
            .catch(async (error: unknown) => {
                // Rejects when the pin expires unauthorized, which is where an
                // unopened popup ends up too.
                authWindow?.close();
                const parsedError = await parseAPIResponseError(error);
                showMessage({
                    level: MessageLevel.error,
                    message: msg(str`Failed to connect source: ${pluckErrorDetail(parsedError)}`),
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
