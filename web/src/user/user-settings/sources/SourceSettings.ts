import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { EVENT_REFRESH } from "@goauthentik/web/constants";
import "@goauthentik/web/elements/EmptyState";
import "@goauthentik/web/user/user-settings/sources/SourceSettingsOAuth";
import "@goauthentik/web/user/user-settings/sources/SourceSettingsPlex";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";

import { SourcesApi, UserSetting } from "@goauthentik/api";

@customElement("ak-user-settings-source")
export class UserSourceSettingsPage extends LitElement {
    @property({ attribute: false })
    sourceSettings?: Promise<UserSetting[]>;

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
    }

    renderSourceSettings(source: UserSetting): TemplateResult {
        switch (source.component) {
            case "ak-user-settings-source-oauth":
                return html`<ak-user-settings-source-oauth
                    class="pf-c-data-list__item-row"
                    objectId=${source.objectUid}
                    title=${source.title}
                    .configureUrl=${source.configureUrl}
                >
                </ak-user-settings-source-oauth>`;
            case "ak-user-settings-source-plex":
                return html`<ak-user-settings-source-plex
                    class="pf-c-data-list__item-row"
                    objectId=${source.objectUid}
                    title=${source.title}
                    .configureUrl=${source.configureUrl}
                >
                </ak-user-settings-source-plex>`;
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
                        return source.map((stage) => {
                            return html`<li class="pf-c-data-list__item">
                                <div class="pf-c-data-list__item-content">
                                    <div class="pf-c-data-list__cell">
                                        <img src="${ifDefined(stage.iconUrl)}" />
                                        ${stage.title}
                                    </div>
                                    <div class="pf-c-data-list__cell">
                                        ${this.renderSourceSettings(stage)}
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
