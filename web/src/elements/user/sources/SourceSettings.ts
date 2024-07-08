import { renderSourceIcon } from "@goauthentik/admin/sources/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/user/sources/SourceSettingsOAuth";
import "@goauthentik/elements/user/sources/SourceSettingsPlex";
import "@goauthentik/elements/user/sources/SourceSettingsSAML";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";

import { PaginatedUserSourceConnectionList, SourcesApi, UserSetting } from "@goauthentik/api";

@customElement("ak-user-settings-source")
export class UserSourceSettingsPage extends AKElement {
    @property({ attribute: false })
    sourceSettings?: UserSetting[];

    @property({ attribute: false })
    connections?: PaginatedUserSourceConnectionList;

    @property({ type: Number })
    userId?: number;

    @property({ type: Boolean })
    canConnect = true;

    static get styles(): CSSResult[] {
        return [
            PFDataList,
            css`
                .pf-c-data-list__cell {
                    display: flex;
                    align-items: center;
                }
                .pf-c-data-list__cell img {
                    max-width: 48px;
                    width: 48px;
                    margin-right: 16px;
                }
                :host([theme="dark"]) .pf-c-data-list__cell img {
                    filter: invert(1);
                }
                .pf-c-data-list__item {
                    background-color: transparent;
                }
            `,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            this.firstUpdated();
        });
    }

    async firstUpdated(): Promise<void> {
        this.sourceSettings = await new SourcesApi(DEFAULT_CONFIG).sourcesAllUserSettingsList();
        this.connections = await new SourcesApi(DEFAULT_CONFIG).sourcesUserConnectionsAllList({
            user: this.userId,
        });
    }

    renderSourceSettings(source: UserSetting): TemplateResult {
        let connectionPk = -1;
        if (this.connections) {
            const connections = this.connections.results.filter(
                (con) => con.source.slug === source.objectUid,
            );
            if (connections.length > 0) {
                connectionPk = connections[0].pk;
            } else {
                connectionPk = 0;
            }
        }
        switch (source.component) {
            case "ak-user-settings-source-oauth":
                return html`<ak-user-settings-source-oauth
                    objectId=${source.objectUid}
                    title=${source.title}
                    connectionPk=${connectionPk}
                    .configureUrl=${this.canConnect ? source.configureUrl : undefined}
                >
                </ak-user-settings-source-oauth>`;
            case "ak-user-settings-source-plex":
                return html`<ak-user-settings-source-plex
                    objectId=${source.objectUid}
                    title=${source.title}
                    connectionPk=${connectionPk}
                    .configureUrl=${this.canConnect ? source.configureUrl : undefined}
                >
                </ak-user-settings-source-plex>`;
            case "ak-user-settings-source-saml":
                return html`<ak-user-settings-source-saml
                    objectId=${source.objectUid}
                    title=${source.title}
                    connectionPk=${connectionPk}
                    .configureUrl=${this.canConnect ? source.configureUrl : undefined}
                >
                </ak-user-settings-source-saml>`;
            default:
                return html`<p>
                    ${msg(str`Error: unsupported source settings: ${source.component}`)}
                </p>`;
        }
    }

    render(): TemplateResult {
        return html` <ul class="pf-c-data-list" role="list">
            ${this.sourceSettings
                ? html`
                      ${this.sourceSettings.length < 1
                          ? html`<ak-empty-state
                                header=${msg("No services available.")}
                            ></ak-empty-state>`
                          : html`
                                ${this.sourceSettings.map((source) => {
                                    return html`<li class="pf-c-data-list__item">
                                        <div class="pf-c-data-list__item-row">
                                            <div class="pf-c-data-list__item-content">
                                                <div class="pf-c-data-list__cell">
                                                    ${renderSourceIcon(
                                                        source.title,
                                                        source.iconUrl,
                                                    )}
                                                    ${source.title}
                                                </div>
                                                <div class="pf-c-data-list__cell">
                                                    ${this.renderSourceSettings(source)}
                                                </div>
                                            </div>
                                        </div>
                                    </li>`;
                                })}
                            `}
                  `
                : html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
                  </ak-empty-state>`}
        </ul>`;
    }
}
