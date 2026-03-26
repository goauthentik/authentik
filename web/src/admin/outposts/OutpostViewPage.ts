import "#elements/Tabs";
import "#admin/events/ObjectChangelog";
import "#admin/rbac/ObjectPermissionsPage";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { outpostTypeToLabel } from "#admin/outposts/utils";

import {
    ModelEnum,
    Outpost,
    OutpostsApi,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues } from "lit";
import { html, nothing } from "lit-html";
import { customElement, property, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-outpost-view")
export class OutpostViewPage extends AKElement {
    @property({ type: String })
    set outpostId(id: string) {
        new OutpostsApi(DEFAULT_CONFIG)
            .outpostsInstancesRetrieve({
                uuid: id,
            })
            .then((outpost) => {
                this.outpost = outpost;
            });
    }

    @state()
    protected outpost: Outpost | null = null;

    static styles: CSSResult[] = [PFGrid, PFPage, PFCard];

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-zone",
            header: this.outpost?.name,
            description: outpostTypeToLabel(this.outpost?.type),
        });
    }

    protected renderTabOverview() {
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
                    aria-label=${msg("Overview")}
                >
                    ${this.renderTabOverview()}
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
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikOutpostsOutpost}
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
