import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { SourcesApi } from "@goauthentik/api";

import { AndNext, DEFAULT_CONFIG } from "../../../api/Config";
import { BaseUserSettings } from "../BaseUserSettings";

@customElement("ak-user-settings-source-oauth")
export class SourceSettingsOAuth extends BaseUserSettings {
    @property()
    title!: string;

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">${t`Source ${this.title}`}</div>
            <div class="pf-c-card__body">${this.renderInner()}</div>
        </div>`;
    }

    renderInner(): TemplateResult {
        return html`${until(
            new SourcesApi(DEFAULT_CONFIG)
                .sourcesUserConnectionsOauthList({
                    sourceSlug: this.objectId,
                })
                .then((connection) => {
                    if (connection.results.length > 0) {
                        return html`<p>${t`Connected.`}</p>
                            <button
                                class="pf-c-button pf-m-danger"
                                @click=${() => {
                                    return new SourcesApi(
                                        DEFAULT_CONFIG,
                                    ).sourcesUserConnectionsOauthDestroy({
                                        id: connection.results[0].pk || 0,
                                    });
                                }}
                            >
                                ${t`Disconnect`}
                            </button>`;
                    }
                    return html`<p>${t`Not connected.`}</p>
                        <a
                            class="pf-c-button pf-m-primary"
                            href="${ifDefined(this.configureUrl)}${AndNext(
                                "/if/user/#/settings;page-sources",
                            )}"
                        >
                            ${t`Connect`}
                        </a>`;
                }),
        )}`;
    }
}
