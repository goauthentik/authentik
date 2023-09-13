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

import { LDAPSource, SourcesApi, Task, TaskStatusEnum } from "@goauthentik/api";

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
    syncState: Task[] = [];

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
                    new SourcesApi(DEFAULT_CONFIG)
                        .sourcesLdapSyncStatusList({
                            slug: this.source.slug,
                        })
                        .then((state) => {
                            this.syncState = state;
                        });
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
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">
                            <p>${msg("Sync status")}</p>
                        </div>
                        <div class="pf-c-card__body">
                            ${this.syncState.length < 1
                                ? html`<p>${msg("Not synced yet.")}</p>`
                                : html`
                                      <ul class="pf-c-list">
                                          ${this.syncState.map((task) => {
                                              let header = "";
                                              if (task.status === TaskStatusEnum.Warning) {
                                                  header = msg("Task finished with warnings");
                                              } else if (task.status === TaskStatusEnum.Error) {
                                                  header = msg("Task finished with errors");
                                              } else {
                                                  header = msg(
                                                      str`Last sync: ${task.taskFinishTimestamp.toLocaleString()}`,
                                                  );
                                              }
                                              return html`<li>
                                                  <p>${task.taskName}</p>
                                                  <ul class="pf-c-list">
                                                      <li>${header}</li>
                                                      ${task.messages.map((m) => {
                                                          return html`<li>${m}</li>`;
                                                      })}
                                                  </ul>
                                              </li> `;
                                          })}
                                      </ul>
                                  `}
                        </div>
                        <div class="pf-c-card__footer">
                            <ak-action-button
                                class="pf-m-secondary"
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
        </ak-tabs>`;
    }
}
