import { renderSourceIcon } from "@goauthentik/admin/sources/SourceViewPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/user/user-settings/sources/SourceSettingsOAuth";
import "@goauthentik/user/user-settings/sources/SourceSettingsPlex";
import "@goauthentik/user/user-settings/sources/SourceSettingsSAML";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";

import { PaginatedUserSourceConnectionList, SourcesApi, UserSetting } from "@goauthentik/api";

@customElement("ak-user-settings-source")
export class UserSourceSettingsPage extends AKElement {
    @property({ attribute: false })
    sourceSettings?: Promise<UserSetting[]>;

    @property({ attribute: false })
    connections?: PaginatedUserSourceConnectionList;

    static get styles(): CSSResult[] {
        return [
            PFDataList,
            PFContent,
            AKGlobal,
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
                @media (prefers-color-scheme: dark) {
                    .pf-c-data-list__cell img {
                        filter: invert(1);
                    }
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

    firstUpdated(): void {
        this.sourceSettings = new SourcesApi(DEFAULT_CONFIG).sourcesAllUserSettingsList();
        new SourcesApi(DEFAULT_CONFIG).sourcesUserConnectionsAllList().then((connections) => {
            this.connections = connections;
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
                return html`<p>${t`Error: unsupported source settings: ${source.component}`}</p>`;
        }
    }

    render(): TemplateResult {
        return html` <div class="pf-c-content">
                <p>
                    ${t`Connect your user account to the services listed below, to allow you to login using the service instead of traditional credentials.`}
                </p>
            </div>
            <ul class="pf-c-data-list" role="list">
                ${until(
                    this.sourceSettings?.then((source) => {
                        if (source.length < 1) {
                            return html`<ak-empty-state
                                header=${t`No services available.`}
                            ></ak-empty-state>`;
                        }
                        return source.map((source) => {
                            return html`<li class="pf-c-data-list__item">
                                <div class="pf-c-data-list__item-content">
                                    <div class="pf-c-data-list__cell">
                                        ${renderSourceIcon(source.title, source.iconUrl)}
                                        ${source.title}
                                    </div>
                                    <div class="pf-c-data-list__cell">
                                        ${this.renderSourceSettings(source)}
                                    </div>
                                </div>
                            </li>`;
                        });
                    }),
                    html`<ak-empty-state ?loading="${true}" header=${t`Loading`}>
                    </ak-empty-state>`,
                )}
            </ul>`;
    }
}
