import "#elements/Spinner";

import { aki } from "#common/api/client";
import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { BaseUserSettings } from "#elements/user/sources/BaseUserSettings";

import { SourcesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-user-settings-source-bsky")
export class SourceSettingsBsky extends BaseUserSettings {
    @state()
    handle = "";

    protected disconnectSource(): Promise<void> {
        return aki(SourcesApi)
            .sourcesUserConnectionsBskyDestroy({
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

        return html`<form
            class="pf-c-form"
            @submit=${(e: SubmitEvent) => {
                e.preventDefault();
                window.location.assign(
                    `${this.configureURL}?identifier=${encodeURIComponent(this.handle)}`,
                );
            }}
        >
            <input
                type="text"
                class="pf-c-form-control"
                placeholder="you.bsky.social"
                required
                .value=${this.handle}
                @input=${(e: InputEvent) => {
                    this.handle = (e.target as HTMLInputElement).value;
                }}
            />
            <button class="pf-c-button pf-m-primary" type="submit">${msg("Connect")}</button>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-source-bsky": SourceSettingsBsky;
    }
}
