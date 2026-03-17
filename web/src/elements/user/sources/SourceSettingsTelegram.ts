import "#elements/Spinner";

import { loadTelegramWidget, TelegramUserResponse } from "../../../flow/sources/telegram/utils";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { BaseUserSettings } from "#elements/user/sources/BaseUserSettings";

import { SourcesApi, UserTelegramSourceConnection } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

@customElement("ak-user-settings-source-telegram")
export class SourceSettingsTelegram extends BaseUserSettings {
    connectBtnRef = createRef();

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

    protected renderConnectButton(): SlottedTemplateResult {
        if (!this.configureURL) {
            return null;
        }

        return html` <div ${ref(this.connectBtnRef)}>
            <button @click=${this.connectTelegram} class="pf-c-button pf-m-primary">
                ${msg("Connect")}
            </button>
        </div>`;
    }

    protected async connectTelegram(): Promise<void> {
        const params = new URLSearchParams(this.configureURL || "");
        const botUsername: string = params.get("bot_username") || "";
        const requestMessageAccess = params.get("request_message_access") === "True";
        if (this.connectBtnRef.value) this.connectBtnRef.value.textContent = "";
        loadTelegramWidget(
            this.connectBtnRef.value,
            botUsername,
            requestMessageAccess,
            (user: TelegramUserResponse) => {
                new SourcesApi(DEFAULT_CONFIG)
                    .sourcesTelegramConnectUserCreate({
                        slug: this.objectId,
                        telegramAuthRequest: {
                            id: user.id,
                            authDate: user.auth_date,
                            hash: user.hash,
                            firstName: user.first_name,
                            lastName: user.last_name,
                            username: user.username,
                            photoUrl: user.photo_url,
                        },
                    })
                    .then((connection: UserTelegramSourceConnection) => {
                        this.connectionPk = connection.pk;
                        showMessage({
                            level: MessageLevel.info,
                            message: msg("Successfully connected source"),
                        });
                    })
                    .catch(async (error: unknown) => {
                        const parsedError = await parseAPIResponseError(error);
                        showMessage({
                            level: MessageLevel.error,
                            message: msg(
                                str`Failed to connect source: ${pluckErrorDetail(parsedError)}`,
                            ),
                        });
                    });
            },
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-source-telegram": SourceSettingsTelegram;
    }
}
