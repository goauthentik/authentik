import "#elements/Spinner";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { BaseUserSettings } from "#elements/user/sources/BaseUserSettings";

import { SourcesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-settings-source-telegram")
export class SourceSettingsTelegram extends BaseUserSettings {
    protected disconnectSource(): Promise<void> {
        return new SourcesApi(DEFAULT_CONFIG)
            .sourcesUserConnectionsTelegramDestroy({
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
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-source-telegram": SourceSettingsTelegram;
    }
}
