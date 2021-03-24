import { customElement, html, TemplateResult } from "lit-element";
import { BaseUserSettings } from "./BaseUserSettings";
import { OAuthSource, SourcesApi } from "authentik-api";
import { until } from "lit-html/directives/until";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { gettext } from "django";
import { AppURLManager } from "../../../api/legacy";

@customElement("ak-user-settings-source-oauth")
export class SourceSettingsOAuth extends BaseUserSettings {

    render(): TemplateResult {
        return html`${until(new SourcesApi(DEFAULT_CONFIG).sourcesOauthRead({
            slug: this.objectId
        }).then((source) => {
            return html`<div class="pf-c-card">
                <div class="pf-pf-c-card__title">
                    ${gettext(`Source ${source.name}`)}
                </div>
                <div class="pf-c-card__body">
                    ${this.renderInner(source)}
                </div>
            </div>`;
        }))}`;
    }

    renderInner(source: OAuthSource): TemplateResult {
        return html`${until(new SourcesApi(DEFAULT_CONFIG).sourcesOauthUserConnectionsList({
            sourceSlug: this.objectId
        }).then((connection) => {
            if (connection.results.length > 0) {
                return html`<p>${gettext("Connected.")}</p>
                <button class="pf-c-button pf-m-danger"
                    @click=${() => {
                        return new SourcesApi(DEFAULT_CONFIG).sourcesOauthUserConnectionsDelete({
                            id: connection.results[0].pk || 0
                        });
                    }}>
                    ${gettext("Disconnect")}
                </button>`;
            }
            return html`<p>${gettext("Not connected.")}</p>
                <a class="pf-c-button pf-m-primary"
                    href=${AppURLManager.sourceOAuth(source.slug, "login")}>
                    ${gettext("Connect")}
                </a>`;
        }))}`;
    }

}
