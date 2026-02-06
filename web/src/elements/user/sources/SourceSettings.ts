import "#elements/EmptyState";
import "#elements/user/sources/SourceSettingsOAuth";
import "#elements/user/sources/SourceSettingsPlex";
import "#elements/user/sources/SourceSettingsSAML";
import "#elements/user/sources/SourceSettingsTelegram";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import Styles from "#elements/user/sources/SourceSettings.css";
import { ifPresent } from "#elements/utils/attributes";

import { renderSourceIcon } from "#admin/sources/utils";

import { SourcesApi, UserSetting, UserSourceConnection } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";

@customElement("ak-user-settings-source")
export class UserSourceSettingsPage extends AKElement {
    static styles: CSSResult[] = [PFDataList, Styles];

    @property({ type: Number, attribute: "user-id" })
    public userId?: number;

    @property({ type: Boolean, attribute: "allow-configuration" })
    public allowConfiguration = false;

    @state()
    protected sourceSettings: UserSetting[] | null = null;

    protected sourceToConnection = new WeakMap<UserSetting, UserSourceConnection>();

    #abortController: AbortController | null = null;

    protected refresh = async () => {
        this.#abortController?.abort();
        this.#abortController = new AbortController();

        const sourcesAPI = new SourcesApi(DEFAULT_CONFIG);

        const [sourceSettings, connections] = await Promise.all([
            sourcesAPI.sourcesAllUserSettingsList({
                signal: this.#abortController?.signal,
            }),
            sourcesAPI.sourcesUserConnectionsAllList(
                {
                    user: this.userId,
                },
                {
                    signal: this.#abortController?.signal,
                },
            ),
        ]);

        if (connections) {
            for (const source of sourceSettings) {
                const matchedConnections = connections.results.filter(
                    (con) => con.sourceObj.slug === source.objectUid,
                );

                if (matchedConnections.length) {
                    if (matchedConnections.length > 1) {
                        console.warn(
                            `Multiple connections found for source ${source.title} (${source.objectUid})`,
                            source,
                            matchedConnections,
                        );
                    }

                    const [connection] = matchedConnections;

                    this.sourceToConnection.set(source, connection);
                }
            }
        }

        this.sourceSettings = sourceSettings;
    };

    public connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener(EVENT_REFRESH, this.refresh);

        // TODO: We need to use a visibility observer to handle when this element
        // is rendered inside a hidden tab or similar.
        this.refresh();
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_REFRESH, this.refresh);
        this.#abortController?.abort();
    }

    renderSourceSettings(source: UserSetting): TemplateResult {
        const { allowConfiguration } = this;
        const connection = this.sourceToConnection.get(source);
        const connectionPk = connection?.pk ?? -1;

        switch (source.component) {
            case "ak-user-settings-source-oauth":
                return html`<ak-user-settings-source-oauth
                    .source=${source}
                    connection-pk=${connectionPk}
                    ?allow-configuration=${allowConfiguration}
                >
                </ak-user-settings-source-oauth>`;
            case "ak-user-settings-source-plex":
                return html`<ak-user-settings-source-plex
                    .source=${source}
                    connection-pk=${connectionPk}
                    ?allow-configuration=${allowConfiguration}
                >
                </ak-user-settings-source-plex>`;
            case "ak-user-settings-source-saml":
                return html`<ak-user-settings-source-saml
                    .source=${source}
                    connection-pk=${connectionPk}
                    ?allow-configuration=${allowConfiguration}
                >
                </ak-user-settings-source-saml>`;
            case "ak-user-settings-source-telegram":
                return html`<ak-user-settings-source-telegram
                    .source=${source}
                    connection-pk=${connectionPk}
                    ?allow-configuration=${allowConfiguration}
                >
                </ak-user-settings-source-telegram>`;
            default:
                return html`<p>
                    ${msg(str`Error: unsupported source settings: ${source.component}`)}
                </p>`;
        }
    }

    protected renderSourceSetting = (source: UserSetting): TemplateResult => {
        const connection = this.sourceToConnection.get(source);
        const connectionPk = connection?.pk ?? -1;
        const connectionUserPk = connection?.user ?? -1;
        return html`<li
            class="pf-c-data-list__item"
            part="list-item"
            aria-label=${msg(str`"${source.title}" source`, {
                id: "source-settings-list-item-label",
            })}
            data-test-id="source-settings-list-item"
            data-slug=${ifPresent(connection?.sourceObj.slug)}
            data-source-uid=${ifPresent(source.objectUid)}
            data-source-component=${ifPresent(source.component)}
            data-connection-pk=${connectionPk}
            data-connection-user-pk=${connectionUserPk}
        >
            <div class="pf-c-data-list__item-row">
                <div class="pf-c-data-list__item-content">
                    <div class="pf-c-data-list__cell">
                        ${renderSourceIcon(
                            source.title,
                            source.iconUrl,
                            source.iconThemedUrls,
                            this.activeTheme,
                        )}
                        ${source.title}
                    </div>
                    <div class="pf-c-data-list__cell">${this.renderSourceSettings(source)}</div>
                </div>
            </div>
        </li>`;
    };

    render(): TemplateResult {
        if (!this.sourceSettings) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        if (this.sourceSettings.length === 0) {
            return html`<ak-empty-state>
                <span>${msg("No services available.")}</span></ak-empty-state
            >`;
        }
        return html`<ul class="pf-c-data-list" part="list" aria-label="${msg("Source Settings")}">
            ${this.sourceSettings.map(this.renderSourceSetting)}
        </ul>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-source": UserSourceSettingsPage;
    }
}
