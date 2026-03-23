import "#admin/blueprints/BlueprintForm";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/ak-mdx/ak-mdx";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import {
    BlueprintInstance,
    BlueprintInstanceStatusEnum,
    ManagedApi,
    ModelEnum,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

export function BlueprintStatus(blueprint?: BlueprintInstance): string {
    if (!blueprint) return "";
    switch (blueprint.status) {
        case BlueprintInstanceStatusEnum.Successful:
            return msg("Successful");
        case BlueprintInstanceStatusEnum.Orphaned:
            return msg("Orphaned");
        case BlueprintInstanceStatusEnum.Warning:
            return msg("Warning");
        case BlueprintInstanceStatusEnum.Error:
            return msg("Error");
    }
    return msg("Unknown");
}

const BlueprintDescriptionProperty = "blueprints.goauthentik.io/description";

export function formatBlueprintDescription(item: BlueprintInstance): string | null {
    const { labels = {} } = (item.metadata || {}) as {
        labels?: Record<string, string | undefined>;
    };

    return labels[BlueprintDescriptionProperty] || null;
}

@customElement("ak-blueprint-list")
export class BlueprintListPage extends TablePage<BlueprintInstance> {
    protected override searchEnabled = true;
    public pageTitle = msg("Blueprints");
    public pageDescription = msg("Automate and template configuration within authentik.");
    public pageIcon = "pf-icon pf-icon-blueprint";

    expandable = true;
    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    async apiEndpoint(): Promise<PaginatedResponse<BlueprintInstance>> {
        return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsList(
            await this.defaultEndpointConfig(),
        );
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Status"), "status"],
        [msg("Last applied"), "last_applied"],
        [msg("Enabled"), "enabled"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Blueprint(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: BlueprintInstance) => {
                return [{ key: msg("Name"), value: item.name }];
            }}
            .usedBy=${(item: BlueprintInstance) => {
                return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsUsedByList({
                    instanceUuid: item.pk,
                });
            }}
            .delete=${(item: BlueprintInstance) => {
                return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsDestroy({
                    instanceUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderExpanded(item: BlueprintInstance): TemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikBlueprintsBlueprintinstance.split(".");

        return html`<dl class="pf-c-description-list pf-m-horizontal">
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${msg("Path")}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            <pre>${item.path}</pre>
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

    row(item: BlueprintInstance): SlottedTemplateResult[] {
        const description = formatBlueprintDescription(item);

        return [
            html`<div>${item.name}</div>
                ${description
                    ? html`<small><ak-mdx .content=${description}></ak-mdx></small>`
                    : nothing}`,
            html`${BlueprintStatus(item)}`,
            Timestamp(item.lastApplied),
            html`<ak-status-label ?good=${item.enabled}></ak-status-label>`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Blueprint")}</span>
                    <ak-blueprint-form slot="form" .instancePk=${item.pk}> </ak-blueprint-form>
                    <button
                        slot="trigger"
                        class="pf-c-button pf-m-plain"
                        aria-label=${msg(str`Edit "${item.name}" blueprint`)}
                    >
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal
                    label=${item.name}
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikBlueprintsBlueprintinstance}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>
                <ak-action-button
                    class="pf-m-plain"
                    label=${msg(str`Apply "${item.name}" blueprint`)}
                    .apiRequest=${() => {
                        return new ManagedApi(DEFAULT_CONFIG)
                            .managedBlueprintsApplyCreate({
                                instanceUuid: item.pk,
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
                    <pf-tooltip position="top" content=${msg("Apply")}>
                        <i class="fas fa-play" aria-hidden="true"></i>
                    </pf-tooltip>
                </ak-action-button>
            </div>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Blueprint Instance")}</span>
                <ak-blueprint-form slot="form"> </ak-blueprint-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-blueprint-list": BlueprintListPage;
    }
}
