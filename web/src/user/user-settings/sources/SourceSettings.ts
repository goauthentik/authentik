import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { SourcesApi, UserSetting } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import { EVENT_REFRESH } from "../../../constants";
import "../../../elements/EmptyState";
import "./SourceSettingsOAuth";
import "./SourceSettingsPlex";

@customElement("ak-user-settings-source")
export class UserSourceSettingsPage extends LitElement {
    @property({ attribute: false })
    sourceSettings?: Promise<UserSetting[]>;

    static get styles(): CSSResult[] {
        return [PFGrid];
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
                    objectId=${source.objectUid}
                    title=${source.title}
                    .configureUrl=${source.configureUrl}
                >
                </ak-user-settings-source-oauth>`;
            case "ak-user-settings-source-plex":
                return html`<ak-user-settings-source-plex
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
        return html`<div class="pf-l-grid pf-m-gutter">
            ${until(
                this.sourceSettings?.then((source) => {
                    if (source.length < 1) {
                        return html`<ak-empty-state
                            header=${t`No services available.`}
                        ></ak-empty-state>`;
                    }
                    return source.map((stage) => {
                        return html`<div class="pf-l-grid__item pf-m-6-col pf-m-4-col-on-xl">
                            ${this.renderSourceSettings(stage)}
                        </div>`;
                    });
                }),
                html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`,
            )}
        </div>`;
    }
}
