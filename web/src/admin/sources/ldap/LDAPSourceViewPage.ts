import "#admin/rbac/ak-rbac-object-permission-page";
import "#admin/sources/ldap/LDAPSourceConnectivity";
import "#admin/sources/ldap/LDAPSourceUserList";
import "#admin/sources/ldap/LDAPSourceGroupList";
import "#admin/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/sync/SyncStatusCard";
import "#elements/tasks/ScheduleList";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { modalInvoker } from "#elements/dialogs";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList from "#components/DescriptionList";

import { LDAPSourceForm } from "#admin/sources/ldap/LDAPSourceForm";

import { LDAPSource, ModelEnum, SourcesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-source-ldap-view")
export class LDAPSourceViewPage extends AKElement {
    @property({ type: String })
    set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesLdapRetrieve({
                slug: slug,
            })
            .then((source) => {
                this.source = source;
            });
    }

    @property({ attribute: false })
    source?: LDAPSource;

    static styles: CSSResult[] = [
        PFPage,
        PFButton,
        PFGrid,
        PFContent,
        PFCard,
        PFDescriptionList,
        PFList,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.source?.slug) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    render(): SlottedTemplateResult {
        if (!this.source) {
            return nothing;
        }
        const [appLabel, modelName] = ModelEnum.AuthentikSourcesLdapLdapsource.split(".");
        return html`<main>
            <ak-tabs>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${msg("Info")}</div>
                            <div class="pf-c-card__body">
                                ${renderDescriptionList(
                                    [
                                        [msg("Name"), html`${this.source?.name}`],
                                        [msg("Server URI"), html`${this.source?.serverUri}`],
                                        [msg("Base DN"), html`${this.source?.baseDn}`],
                                        [
                                            msg("Status"),
                                            html`<ak-status-label
                                                type="neutral"
                                                ?good=${this.source?.enabled}
                                                good-label=${msg("Enabled")}
                                                bad-label=${msg("Disabled")}
                                            ></ak-status-label>`,
                                        ],
                                        [
                                            msg("Related actions"),
                                            html`<button
                                                class="pf-c-button pf-m-primary pf-m-block"
                                                ${modalInvoker(LDAPSourceForm, {
                                                    instancePk: this.source?.slug,
                                                })}
                                            >
                                                ${msg("Edit")}
                                            </button>`,
                                        ],
                                    ],
                                    { twocolumn: true },
                                )}
                            </div>
                        </div>
                        <div class="pf-l-grid__item pf-m-12-col pf-m-6-col-on-xl pf-m-6-col-on-2xl">
                            <ak-sync-status-card
                                .fetch=${() => {
                                    if (!this.source) return Promise.reject();
                                    return new SourcesApi(
                                        DEFAULT_CONFIG,
                                    ).sourcesLdapSyncStatusRetrieve({
                                        slug: this.source.slug,
                                    });
                                }}
                            ></ak-sync-status-card>
                        </div>
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__title">
                                <p>${msg("Connectivity")}</p>
                            </div>
                            <div class="pf-c-card__body">
                                <ak-source-ldap-connectivity
                                    .connectivity=${this.source?.connectivity}
                                ></ak-source-ldap-connectivity>
                            </div>
                        </div>
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__title">
                                <p>${msg("Schedules")}</p>
                            </div>
                            <ak-schedule-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${this.source?.pk}"
                            ></ak-schedule-list>
                        </div>
                    </div>
                </div>
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-users"
                    id="page-users"
                    aria-label="${msg("Synced Users")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <ak-source-ldap-users-list
                            .source=${this.source}
                        ></ak-source-ldap-users-list>
                    </div>
                </section>
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-groups"
                    id="page-groups"
                    aria-label="${msg("Synced Groups")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <ak-source-ldap-groups-list
                            .source=${this.source}
                        ></ak-source-ldap-groups-list>
                    </div>
                </section>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-changelog"
                    id="page-changelog"
                    aria-label="${msg("Changelog")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <ak-object-changelog
                                targetModelPk=${this.source?.pk || ""}
                                targetModelName=${ModelEnum.AuthentikSourcesLdapLdapsource}
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${ModelEnum.AuthentikSourcesLdapLdapsource}
                    objectPk=${this.source?.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-view": LDAPSourceViewPage;
    }
}
