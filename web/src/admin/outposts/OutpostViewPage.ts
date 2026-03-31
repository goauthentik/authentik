import "#elements/Tabs";
import "#admin/events/ObjectChangelog";
import "#admin/rbac/ak-rbac-object-permission-page";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";
import "#admin/outposts/OutpostForm";
import "#admin/outposts/OutpostHealthList";
import "#admin/outposts/OutpostProviderList";
import "#elements/buttons/TokenCopyButton/ak-token-copy-button";

import { DEFAULT_CONFIG } from "#common/api/config";
import { docLink } from "#common/global";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";
import renderDescriptionList from "#components/DescriptionList";

import { OutpostForm } from "#admin/outposts/OutpostForm";
import { embeddedOutpostManaged, outpostTypeToLabel } from "#admin/outposts/utils";

import { ModelEnum, Outpost, OutpostHealth, OutpostsApi, OutpostTypeEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, PropertyValues } from "lit";
import { html } from "lit-html";
import { guard } from "lit-html/directives/guard.js";
import { customElement, property } from "lit/decorators.js";
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
    public static styles: CSSResult[] = [
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

    #api = new OutpostsApi(DEFAULT_CONFIG);

    @property({ type: String, attribute: "outpost-id" })
    set outpostID(id: string) {
        this.#api.outpostsInstancesRetrieve({ uuid: id }).then((outpost) => {
            this.outpost = outpost;

            return this.#api
                .outpostsInstancesHealthList({
                    uuid: outpost.pk,
                })
                .then((health) => {
                    this.health = health;
                });
        });
    }

    @property({ attribute: false })
    public outpost: Outpost | null = null;

    @property({ attribute: false })
    public health: OutpostHealth[] = [];

    protected openEditModal() {
        if (!this.outpost) return;

        const form = new OutpostForm();

        form.instancePk = this.outpost.pk;
        form.embedded = this.outpost.managed === embeddedOutpostManaged;

        return form.showModal();
    }

    protected override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        if (changed.has("outpost") && this.outpost) {
            setPageDetails({
                icon: "pf-icon pf-icon-zone",
                header: this.outpost?.name,
                description: outpostTypeToLabel(this.outpost?.type),
            });
        }
    }

    protected renderHealthSummary(): SlottedTemplateResult {
        return guard([this.health], () => {
            const totalCount = this.health.length;

            if (!totalCount) {
                return msg("-");
            }

            let healthyCount = 0;
            let unhealthyCount = 0;

            for (const h of this.health) {
                if (h.versionOutdated) {
                    unhealthyCount++;
                } else {
                    healthyCount++;
                }
            }

            const healthyPct = (100 / totalCount) * healthyCount;
            const unhealthyPct = (100 / totalCount) * unhealthyCount;

            return html`<div class="pf-c-progress pf-m-inside">
                <div
                    class="pf-c-progress__bar"
                    role="progressbar"
                    aria-valuemin="0"
                    aria-valuemax=${totalCount}
                    aria-valuenow=${totalCount}
                >
                    ${healthyPct
                        ? html`
                              <div class="pf-c-progress__indicator" style="width: ${healthyPct}%;">
                                  <span class="pf-c-progress__measure">${healthyPct}%</span>
                              </div>
                          `
                        : null}
                    ${unhealthyPct
                        ? html`<div
                              class="pf-c-progress__indicator pf-m-success"
                              style="width: ${unhealthyPct}%; margin-left: ${healthyPct}%; background-color: var(--pf-c-progress--m-warning__bar--BackgroundColor);"
                          >
                              <span class="pf-c-progress__measure">${unhealthyPct}%</span>
                          </div>`
                        : null}
                </div>
            </div>`;
        });
    }

    protected renderTabOverview(): SlottedTemplateResult {
        return html`
            ${(this.outpost?.config.authentik_host ?? "") === ""
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg(
                          "Warning: authentik Domain is not configured, authentication will not work.",
                      )}
                  </div>`
                : null}
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
                                html`<button
                                    @click=${this.openEditModal}
                                    class="pf-c-button pf-m-block pf-m-secondary"
                                    aria-label=${msg(
                                        str`Edit "${this.outpost?.name || "outpost"}"`,
                                    )}
                                >
                                    ${msg("Edit")}
                                </button>`,
                            ],
                        ])}
                    </div>
                </div>
                <div
                    class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                >
                    <div class="pf-c-card__title">${msg("Configured providers")}</div>
                    <ak-outposts-provider-list
                        .items=${this.outpost?.providersObj}
                    ></ak-outposts-provider-list>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">
                        ${msg("Detailed health (data is cached so may be out of date)")}
                    </div>
                    <ak-outpost-health-list .items=${this.health}></ak-outpost-health-list>
                </div>
                ${this.renderOutpostDeploymentInfo()}
            </div>
        `;
    }

    protected renderOutpostDeploymentInfo(): SlottedTemplateResult {
        if (this.outpost?.managed === embeddedOutpostManaged) {
            return null;
        }

        return html`<div class="pf-c-card pf-l-grid__item pf-m-12-col">
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
                            <span class="pf-c-form__label-text">AUTHENTIK_HOST</span>
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
                            <span class="pf-c-form__label-text">AUTHENTIK_TOKEN</span>
                        </label>
                        <div>
                            <ak-token-copy-button
                                class="pf-m-primary"
                                identifier="${ifDefined(this.outpost?.tokenIdentifier)}"
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
                            <span class="pf-c-form__label-text">AUTHENTIK_INSECURE</span>
                        </label>
                        <input class="pf-c-form-control" readonly type="text" value="true" />
                    </div>
                    ${this.outpost?.type === OutpostTypeEnum.Proxy
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
                        : null}
                </form>
            </div>
        </div>`;
    }

    protected renderTabTasks(): SlottedTemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikOutpostsOutpost.split(".");

        return html`<div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                <div class="pf-c-card">
                    <div class="pf-c-card__header">
                        <div class="pf-c-card__title">${msg("Schedules")}</div>
                    </div>
                    <ak-schedule-list
                        .relObjAppLabel=${appLabel}
                        .relObjModel=${modelName}
                        .relObjId="${this.outpost?.pk}"
                    ></ak-schedule-list>
                </div>
            </div>
            <div class="pf-l-grid__item pf-m-12-col pf-l-stack__item">
                <div class="pf-c-card">
                    <div class="pf-c-card__header">
                        <div class="pf-c-card__title">${msg("Tasks")}</div>
                    </div>
                    <ak-task-list
                        .relObjAppLabel=${appLabel}
                        .relObjModel=${modelName}
                        .relObjId="${this.outpost?.pk}"
                    ></ak-task-list>
                </div>
            </div>
        </div> `;
    }

    render() {
        if (!this.outpost) {
            return null;
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
                        <ak-object-changelog
                            targetModelPk=${this.outpost?.pk || ""}
                            targetModelName=${ModelEnum.AuthentikOutpostsOutpost}
                        >
                        </ak-object-changelog>
                    </div>
                </div>
                <ak-rbac-object-permission-page
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
