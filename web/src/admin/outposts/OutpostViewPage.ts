import "#elements/Tabs";
import "#admin/events/ObjectChangelog";
import "#admin/rbac/ObjectPermissionsPage";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";
import "#admin/outposts/OutpostForm";
import "#admin/outposts/OutpostProviderList";
import "../../elements/buttons/TokenCopyButton/ak-token-copy-button";

import { DEFAULT_CONFIG } from "#common/api/config";
import { docLink } from "#common/global";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";
import renderDescriptionList from "#components/DescriptionList";

import { embeddedOutpostManaged, outpostTypeToLabel } from "#admin/outposts/utils";

import { ModelEnum, Outpost, OutpostHealth, OutpostsApi, OutpostTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues } from "lit";
import { html, nothing } from "lit-html";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFProgress from "@patternfly/patternfly/components/Progress/progress.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-outpost-view")
export class OutpostViewPage extends AKElement {
    @property({ type: String })
    set outpostId(id: string) {
        const api = new OutpostsApi(DEFAULT_CONFIG);
        api.outpostsInstancesRetrieve({
            uuid: id,
        }).then((outpost) => {
            this.outpost = outpost;
            api.outpostsInstancesHealthList({
                uuid: outpost.pk,
            }).then((health) => {
                this.health = health;
            });
        });
    }

    @state()
    protected outpost: Outpost | null = null;

    @state()
    protected health: OutpostHealth[] = [];

    static styles: CSSResult[] = [
        PFGrid,
        PFForm,
        PFFormControl,
        PFPage,
        PFBanner,
        PFCard,
        PFDescriptionList,
        PFButton,
        PFProgress,
    ];

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-zone",
            header: this.outpost?.name,
            description: outpostTypeToLabel(this.outpost?.type),
        });
    }

    renderHealthSummary() {
        if (!this.health || this.health.length < 1) {
            return html`-`;
        }
        const totalCount = this.health.length;
        let healthyCount = 0;
        let unhealthyCount = 0;
        this.health.forEach((h) => {
            if (h.versionOutdated) {
                unhealthyCount++;
            } else {
                healthyCount++;
            }
        });
        const healthyPct = (100 / totalCount) * healthyCount;
        const unhealthyPct = (100 / totalCount) * unhealthyCount;
        return html`<div class="pf-c-progress pf-m-inside">
            <div
                class="pf-c-progress__bar"
                role="progressbar"
                aria-valuemin="0"
                aria-valuemax="${totalCount}"
                aria-valuenow="${totalCount}"
            >
                ${healthyPct > 0
                    ? html`
                          <div class="pf-c-progress__indicator" style="width: ${healthyPct}%;">
                              <span class="pf-c-progress__measure">${healthyPct}%</span>
                          </div>
                      `
                    : nothing}
                ${unhealthyPct > 0
                    ? html`<div
                          class="pf-c-progress__indicator pf-m-success"
                          style="width: ${unhealthyPct}%; margin-left: ${healthyPct}%; background-color: var(--pf-c-progress--m-warning__bar--BackgroundColor);"
                      >
                          <span class="pf-c-progress__measure">${unhealthyPct}%</span>
                      </div>`
                    : nothing}
            </div>
        </div>`;
    }

    protected renderTabOverview() {
        return html`
            ${(this.outpost?.config.authentik_host ?? "") === ""
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg(
                          "Warning: authentik Domain is not configured, authentication will not work.",
                      )}
                  </div>`
                : nothing}
            <div class="pf-l-grid pf-m-gutter pf-c-page__main-section pf-m-no-padding-mobile">
                <div
                    class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-3-col-on-xl pf-m-3-col-on-2xl"
                >
                    <div class="pf-c-card__title">${msg("Outpost Info")}</div>
                    <div class="pf-c-card__body">
                        ${renderDescriptionList([
                            [msg("Name"), this.outpost?.name],
                            [msg("Type"), outpostTypeToLabel(this.outpost?.type)],
                            [
                                msg("Integration"),
                                this.outpost?.serviceConnectionObj?.name ||
                                    msg("No integration active"),
                            ],
                            [msg("Health"), this.renderHealthSummary()],
                            [
                                msg("Related actions"),
                                html`<ak-forms-modal>
                                    <span slot="submit">${msg("Save Changes")}</span>
                                    <span slot="header">${msg("Update Outpost")}</span>
                                    <ak-outpost-form
                                        slot="form"
                                        .instancePk=${this.outpost?.pk}
                                        .embedded=${this.outpost?.managed ===
                                        embeddedOutpostManaged}
                                    >
                                    </ak-outpost-form>
                                    <button
                                        slot="trigger"
                                        class="pf-c-button pf-m-block pf-m-secondary"
                                    >
                                        ${msg("Edit")}
                                    </button>
                                </ak-forms-modal>`,
                            ],
                        ])}
                    </div>
                </div>
                <div class="pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl">
                    <ak-outposts-provider-list .outpost=${this.outpost}></ak-outposts-provider-list>
                </div>
                ${this.outpost?.managed !== embeddedOutpostManaged
                    ? html`<div class="pf-c-card pf-l-grid__item pf-m-12-col">
                              <div class="pf-c-card__title">${msg("Outpost Deployment Info")}</div>
                              <div class="pf-c-card__body">
                                  <p>
                                      <a
                                          target="_blank"
                                          href=${docLink("/add-secure-apps/outposts#deploy")}
                                          rel="noopener noreferrer"
                                          >${msg("View deployment documentation")}</a
                                      >
                                  </p>
                                  <form class="pf-c-form">
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >AUTHENTIK_HOST</span
                                              >
                                          </label>
                                          <input
                                              class="pf-c-form-control"
                                              readonly
                                              type="text"
                                              value="${document.location.origin}"
                                          />
                                      </div>
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >AUTHENTIK_TOKEN</span
                                              >
                                          </label>
                                          <div>
                                              <ak-token-copy-button
                                                  class="pf-m-primary"
                                                  identifier="${ifDefined(
                                                      this.outpost?.tokenIdentifier,
                                                  )}"
                                              >
                                                  ${msg("Click to copy token")}
                                              </ak-token-copy-button>
                                          </div>
                                      </div>
                                      <h3>
                                          ${msg(
                                              "If your authentik Instance is using a self-signed certificate, set this value.",
                                          )}
                                      </h3>
                                      <div class="pf-c-form__group">
                                          <label class="pf-c-form__label">
                                              <span class="pf-c-form__label-text"
                                                  >AUTHENTIK_INSECURE</span
                                              >
                                          </label>
                                          <input
                                              class="pf-c-form-control"
                                              readonly
                                              type="text"
                                              value="true"
                                          />
                                      </div>
                                      ${
                                          this.outpost?.type === OutpostTypeEnum.Proxy
                                              ? html`
                                                    <h3>
                                                        ${msg(
                                                            "If your authentik_host setting does not match the URL you want to login with, add this setting.",
                                                        )}
                                                    </h3>
                                                    <div class="pf-c-form__group">
                                                        <label class="pf-c-form__label">
                                                            <span class="pf-c-form__label-text"
                                                                >AUTHENTIK_HOST_BROWSER</span
                                                            >
                                                        </label>
                                                        <input
                                                            class="pf-c-form-control"
                                                            readonly
                                                            type="text"
                                                            value="${document.location.origin}"
                                                        />
                                                    </div>
                                                `
                                              : nothing
                                      }
                                  </form>
                              </div>
                          </div>
                          </div>`
                    : nothing}
            </div>
        `;
    }

    protected renderTabTasks() {
        const [appLabel, modelName] = ModelEnum.AuthentikOutpostsOutpost.split(".");
        return html`<div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                <div class="pf-c-card">
                    <div class="pf-c-card__header">
                        <div class="pf-c-card__title">${msg("Schedules")}</div>
                    </div>
                    <div class="pf-c-card__body">
                        <ak-schedule-list
                            .relObjAppLabel=${appLabel}
                            .relObjModel=${modelName}
                            .relObjId="${this.outpost?.pk}"
                        ></ak-schedule-list>
                    </div>
                </div>
            </div>
            <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                <div class="pf-c-card">
                    <div class="pf-c-card__header">
                        <div class="pf-c-card__title">${msg("Tasks")}</div>
                    </div>
                    <div class="pf-c-card__body">
                        <ak-task-list
                            .relObjAppLabel=${appLabel}
                            .relObjModel=${modelName}
                            .relObjId="${this.outpost?.pk}"
                        ></ak-task-list>
                    </div>
                </div>
            </div>
        </div> `;
    }

    render() {
        if (!this.outpost) {
            return nothing;
        }
        return html`<main>
            <ak-tabs>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                >
                    ${this.renderTabOverview()}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-tasks"
                    id="page-tasks"
                    aria-label=${msg("Tasks")}
                >
                    ${this.renderTabTasks()}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-changelog"
                    id="page-changelog"
                    aria-label="${msg("Changelog")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.outpost?.pk || ""}
                                targetModelApp="authentik_outposts"
                                targetModelName="outpost"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
                <ak-rbac-object-permission-page
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${ModelEnum.AuthentikOutpostsOutpost}
                    objectPk=${this.outpost.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }
}
declare global {
    interface HTMLElementTagNameMap {
        "ak-outpost-view": OutpostViewPage;
    }
}
