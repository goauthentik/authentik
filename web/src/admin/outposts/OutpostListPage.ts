import "#admin/outposts/OutpostDeploymentModal";
import "#admin/outposts/OutpostForm";
import "#admin/outposts/OutpostHealth";
import "#admin/outposts/OutpostHealthSimple";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import {
    ModelEnum,
    Outpost,
    OutpostHealth,
    OutpostsApi,
    OutpostTypeEnum,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

export function TypeToLabel(type?: OutpostTypeEnum): string {
    if (!type) return "";
    switch (type) {
        case OutpostTypeEnum.Proxy:
            return msg("Proxy");
        case OutpostTypeEnum.Ldap:
            return msg("LDAP");
        case OutpostTypeEnum.Radius:
            return msg("Radius");
        case OutpostTypeEnum.Rac:
            return msg("RAC");
        case OutpostTypeEnum.UnknownDefaultOpenApi:
            return msg("Unknown type");
    }
}

@customElement("ak-outpost-list")
export class OutpostListPage extends TablePage<Outpost> {
    expandable = true;

    public pageTitle = msg("Outposts");
    public pageDescription = msg(
        "Outposts are deployments of authentik components to support different environments and protocols, like reverse proxies.",
    );

    public pageIcon = "pf-icon pf-icon-zone";
    protected override searchEnabled = true;

    async apiEndpoint(): Promise<PaginatedResponse<Outpost>> {
        const outposts = await new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesList(
            await this.defaultEndpointConfig(),
        );
        await Promise.all(
            outposts.results.map((outpost) => {
                return new OutpostsApi(DEFAULT_CONFIG)
                    .outpostsInstancesHealthList({
                        uuid: outpost.pk,
                    })
                    .then((health) => {
                        this.health[outpost.pk] = health;
                    });
            }),
        );
        return outposts;
    }

    @state()
    health: { [key: string]: OutpostHealth[] } = {};

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type"), "type"],
        [msg("Providers")],
        [msg("Integration"), "service_connection__name"],
        [msg("Health and Version")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    row(item: Outpost): SlottedTemplateResult[] {
        return [
            html`<div>${item.name}</div>
                ${item.config.authentik_host === ""
                    ? html`<ak-label color=${PFColor.Orange} compact>
                          ${msg(
                              "Warning: authentik Domain is not configured, authentication will not work.",
                          )}
                      </ak-label>`
                    : html`<ak-label color=${PFColor.Green} compact>
                          ${msg(str`Logging in via ${item.config.authentik_host}.`)}
                      </ak-label>`}`,
            html`${TypeToLabel(item.type)}`,
            html`<ul>
                ${item.providersObj?.map((p) => {
                    return html`<li>
                        <a href="#/core/providers/${p.pk}">${p.name}</a>
                    </li>`;
                })}
            </ul>`,
            html`${item.serviceConnectionObj?.name || msg("No integration active")}`,
            html`<ak-outpost-health-simple
                outpostId=${ifDefined(item.pk)}
            ></ak-outpost-health-simple>`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Outpost")}</span>
                    <ak-outpost-form
                        slot="form"
                        .instancePk=${item.pk}
                        .embedded=${item.managed === "goauthentik.io/outposts/embedded"}
                    >
                    </ak-outpost-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikOutpostsOutpost}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>
                ${item.managed !== "goauthentik.io/outposts/embedded"
                    ? html`<ak-outpost-deployment-modal .outpost=${item} size=${PFSize.Medium}>
                          <button slot="trigger" class="pf-c-button pf-m-tertiary">
                              ${msg("View Deployment Info")}
                          </button>
                      </ak-outpost-deployment-modal>`
                    : nothing}
            </div>`,
        ];
    }

    renderExpanded(item: Outpost): TemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikOutpostsOutpost.split(".");
        return html` <h3>
                ${msg(
                    "Detailed health (one instance per column, data is cached so may be out of date)",
                )}
            </h3>
            <dl class="pf-c-description-list pf-m-3-col-on-lg">
                ${this.health[item.pk].map((h) => {
                    return html`<div class="pf-c-description-list__group">
                        <dd class="pf-c-description-list__description">
                            <div class="pf-c-description-list__text">
                                <ak-outpost-health .outpostHealth=${h}></ak-outpost-health>
                            </div>
                        </dd>
                    </div>`;
                })}
            </dl>
            <dl class="pf-c-description-list pf-m-horizontal">
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${msg("Schedules")}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            <ak-schedule-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${item.pk}"
                            ></ak-schedule-list>
                        </div>
                    </dd>
                </div>
            </dl>
            <dl class="pf-c-description-list pf-m-horizontal">
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${msg("Tasks")}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            <ak-task-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${item.pk}"
                            ></ak-task-list>
                        </div>
                    </dd>
                </div>
            </dl>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Outpost(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Outpost) => {
                return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesUsedByList({
                    uuid: item.pk,
                });
            }}
            .delete=${(item: Outpost) => {
                return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesDestroy({
                    uuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Outpost")}</span>
                <ak-outpost-form slot="form"> </ak-outpost-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-outpost-list": OutpostListPage;
    }
}
