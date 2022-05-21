import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { SourcesApi } from "@goauthentik/api";

import { AndNext, DEFAULT_CONFIG } from "../../../api/Config";
import { MessageLevel } from "../../../elements/messages/Message";
import { showMessage } from "../../../elements/messages/MessageContainer";
import { BaseUserSettings } from "../BaseUserSettings";

@customElement("ak-user-settings-source-oauth")
export class SourceSettingsOAuth extends BaseUserSettings {
    @property()
    title!: string;

    render(): TemplateResult {
        return html`${until(
            new SourcesApi(DEFAULT_CONFIG)
                .sourcesUserConnectionsOauthList({
                    sourceSlug: this.objectId,
                })
                .then((connection) => {
                    if (connection.results.length > 0) {
                        return html` <button
                            class="pf-c-button pf-m-danger"
                            @click=${() => {
                                return new SourcesApi(DEFAULT_CONFIG)
                                    .sourcesUserConnectionsOauthDestroy({
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
                    return html` <a
                        class="pf-c-button pf-m-primary"
                        href="${ifDefined(this.configureUrl)}${AndNext(
                            `/if/user/#/settings;${JSON.stringify({ page: "page-sources" })}`,
                        )}"
                    >
                        ${t`Connect`}
                    </a>`;
                }),
        )}`;
    }
}
