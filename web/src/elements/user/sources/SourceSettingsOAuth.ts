import "#elements/Spinner";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { BaseUserSettings } from "#elements/user/sources/BaseUserSettings";

import { toUserSettings } from "#user/navigation";

import { applyNextParam } from "#admin/flows/utils";

import { SourcesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-settings-source-oauth")
export class SourceSettingsOAuth extends BaseUserSettings {
    @property()
    title!: string;

    @property({ type: Number })
    connectionPk = 0;

    render(): TemplateResult {
        if (this.connectionPk === -1) {
            return html`<ak-spinner></ak-spinner>`;
        }
        if (this.connectionPk > 0) {
            return html`<button
                class="pf-c-button pf-m-danger"
                @click=${() => {
                    return new SourcesApi(DEFAULT_CONFIG)
                        .sourcesUserConnectionsOauthDestroy({
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
                }}
            >
                ${msg("Disconnect")}
            </button>`;
        }
        if (this.configureUrl) {
            const target = new URL(this.configureUrl);

            const destination = toUserSettings();

            applyNextParam(target, destination);

            return html`<a class="pf-c-button pf-m-primary" href="${target}">
                ${msg("Connect")}
            </a>`;
        }
        return html`${msg("-")}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-source-oauth": SourceSettingsOAuth;
    }
}
