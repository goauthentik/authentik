import { renderSourceIcon } from "@goauthentik/admin/sources/SourceViewPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { me } from "@goauthentik/common/users";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/user/user-settings/sources/SourceSettingsOAuth";
import "@goauthentik/user/user-settings/sources/SourceSettingsPlex";
import "@goauthentik/user/user-settings/sources/SourceSettingsSAML";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";

import { PaginatedUserSourceConnectionList, SourcesApi, UserSetting } from "@goauthentik/api";

@customElement("ak-user-settings-source")
export class UserSourceSettingsPage extends AKElement {
    @property({ attribute: false })
    sourceSettings?: UserSetting[];

    @property({ attribute: false })
    connections?: PaginatedUserSourceConnectionList;

    static get styles(): CSSResult[] {
        return [
            PFDataList,
            PFContent,
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
        const user = await me();
        this.sourceSettings = await new SourcesApi(DEFAULT_CONFIG).sourcesAllUserSettingsList();
        this.connections = await new SourcesApi(DEFAULT_CONFIG).sourcesUserConnectionsAllList({
            user: user.user.pk,
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
                    class="pf-c-data-list__item-row"
                    objectId=${source.objectUid}
                    title=${source.title}
                    connectionPk=${connectionPk}
                    .configureUrl=${source.configureUrl}
                >
                </ak-user-settings-source-oauth>`;
            case "ak-user-settings-source-plex":
                return html`<ak-user-settings-source-plex
                    class="pf-c-data-list__item-row"
                    objectId=${source.objectUid}
                    title=${source.title}
                    connectionPk=${connectionPk}
                    .configureUrl=${source.configureUrl}
                >
                </ak-user-settings-source-plex>`;
            case "ak-user-settings-source-saml":
                return html`<ak-user-settings-source-saml
                    class="pf-c-data-list__item-row"
                    objectId=${source.objectUid}
                    title=${source.title}
                    connectionPk=${connectionPk}
                    .configureUrl=${source.configureUrl}
                >
                </ak-user-settings-source-saml>`;
            default:
                return html`<p>
                    ${msg(str`Error: unsupported source settings: ${source.component}`)}
                </p>`;
        }
    }

    render(): TemplateResult {
        return html` <div class="pf-c-content">
                <p>
                    ${msg(
                        "Connect your user account to the services listed below, to allow you to login using the service instead of traditional credentials.",
                    )}
                </p>
            </div>
            <ul class="pf-c-data-list" role="list">
                ${this.sourceSettings
                    ? html`
                          ${this.sourceSettings.length < 1
                              ? html`<ak-empty-state
                                    header=${msg("No services available.")}
                                ></ak-empty-state>`
                              : html`
                                    ${this.sourceSettings.map((source) => {
                                        return html`<li class="pf-c-data-list__item">
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
                                        </li>`;
                                    })}
                                `}
                      `
                    : html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
                      </ak-empty-state>`}
            </ul>`;
    }
}
