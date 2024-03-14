import "@goauthentik/admin/sources/ldap/LDAPSourceConnectivity";
import "@goauthentik/admin/sources/ldap/LDAPSourceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/rbac/ObjectPermissionsPage";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    LDAPSource,
    LDAPSyncStatus,
    RbacPermissionsAssignedByUsersListModelEnum,
    SourcesApi,
    SystemTaskStatusEnum,
} from "@goauthentik/api";

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
    source!: LDAPSource;

    @state()
    syncState?: LDAPSyncStatus;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFButton, PFGrid, PFContent, PFCard, PFDescriptionList, PFList];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.source?.slug) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    renderSyncStatus(): TemplateResult {
        if (!this.syncState) {
            return html`${msg("No sync status.")}`;
        }
        if (this.syncState.isRunning) {
            return html`${msg("Sync currently running.")}`;
        }
        if (this.syncState.tasks.length < 1) {
            return html`${msg("Not synced yet.")}`;
        }
        return html`
            <ul class="pf-c-list">
                ${this.syncState.tasks.map((task) => {
                    let header = "";
                    if (task.status === SystemTaskStatusEnum.Warning) {
                        header = msg("Task finished with warnings");
                    } else if (task.status === SystemTaskStatusEnum.Error) {
                        header = msg("Task finished with errors");
                    } else {
                        header = msg(str`Last sync: ${task.finishTimestamp.toLocaleString()}`);
                    }
                    return html`<li>
                        <p>${task.name}</p>
                        <ul class="pf-c-list">
                            <li>${header}</li>
                            ${task.messages.map((m) => {
                                return html`<li>${m}</li>`;
                            })}
                        </ul>
                    </li> `;
                })}
            </ul>
        `;
    }

    load(): void {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesLdapSyncStatusRetrieve({
                slug: this.source.slug,
            })
            .then((state) => {
                this.syncState = state;
            });
    }

    render(): TemplateResult {
        if (!this.source) {
            return html``;
        }
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
                @activate=${() => {
                    this.load();
                }}
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__body">
                            <dl class="pf-c-description-list pf-m-2-col-on-lg">
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${msg("Name")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.source.name}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${msg("Server URI")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.source.serverUri}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${msg("Base DN")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <ul>
                                                <li>${this.source.baseDn}</li>
                                            </ul>
                                        </div>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                        <div class="pf-c-card__footer">
                            <ak-forms-modal>
                                <span slot="submit"> ${msg("Update")} </span>
                                <span slot="header"> ${msg("Update LDAP Source")} </span>
                                <ak-source-ldap-form slot="form" .instancePk=${this.source.slug}>
                                </ak-source-ldap-form>
                                <button slot="trigger" class="pf-c-button pf-m-primary">
                                    ${msg("Edit")}
                                </button>
                            </ak-forms-modal>
                        </div>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-2-col">
                        <div class="pf-c-card__title">
                            <p>${msg("Connectivity")}</p>
                        </div>
                        <div class="pf-c-card__body">
                            <ak-source-ldap-connectivity
                                .connectivity=${this.source.connectivity}
                            ></ak-source-ldap-connectivity>
                        </div>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-10-col">
                        <div class="pf-c-card__title">
                            <p>${msg("Sync status")}</p>
                        </div>
                        <div class="pf-c-card__body">${this.renderSyncStatus()}</div>
                        <div class="pf-c-card__footer">
                            <ak-action-button
                                class="pf-m-secondary"
                                ?disabled=${this.syncState?.isRunning}
                                .apiRequest=${() => {
                                    return new SourcesApi(DEFAULT_CONFIG)
                                        .sourcesLdapPartialUpdate({
                                            slug: this.source?.slug || "",
                                            patchedLDAPSourceRequest: this.source,
                                        })
                                        .then(() => {
                                            this.dispatchEvent(
                                                new CustomEvent(EVENT_REFRESH, {
                                                    bubbles: true,
                                                    composed: true,
                                                }),
                                            );
                                            this.load();
                                        });
                                }}
                            >
                                ${msg("Run sync again")}
                            </ak-action-button>
                        </div>
                    </div>
                </div>
            </section>
            <section
                slot="page-changelog"
                data-tab-title="${msg("Changelog")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.source.pk || ""}
                                targetModelApp="authentik_sources_ldap"
                                targetModelName="ldapsource"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.SourcesLdapLdapsource}
                objectPk=${this.source.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }
}
