import { customElement, html, property, TemplateResult } from "lit-element";
import { BaseUserSettings } from "../BaseUserSettings";
import { SourcesApi } from "@goauthentik/api";
import { until } from "lit-html/directives/until";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { t } from "@lingui/macro";

@customElement("ak-user-settings-source-plex")
export class SourceSettingsPlex extends BaseUserSettings {
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
                .sourcesUserConnectionsPlexList({
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
                                    ).sourcesUserConnectionsPlexDestroy({
                                        id: connection.results[0].pk || 0,
                                    });
                                }}
                            >
                                ${t`Disconnect`}
                            </button>`;
                    }
                    return html`<p>${t`Not connected.`}</p>`;
                }),
        )}`;
    }
}
