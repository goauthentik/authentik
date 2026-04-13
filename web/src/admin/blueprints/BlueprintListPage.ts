import "#admin/blueprints/BlueprintForm";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#admin/blueprints/BlueprintImportForm";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/ak-mdx/ak-mdx";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { docLink } from "#common/global";

import { IconEditButton, modalInvoker, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { BlueprintForm } from "#admin/blueprints/BlueprintForm";

import {
    BlueprintInstance,
    BlueprintInstanceStatusEnum,
    ManagedApi,
    ModelEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { customElement } from "lit/decorators.js";

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
    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    protected override searchEnabled = true;

    public pageTitle = msg("Blueprints");
    public pageDescription = msg("Automate and template configuration within authentik.");
    public pageIcon = "pf-icon pf-icon-blueprint";

    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for a blueprint by name or path...");

    public override order = "name";

    protected override async apiEndpoint(): Promise<PaginatedResponse<BlueprintInstance>> {
        return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsList(
            await this.defaultEndpointConfig(),
        );
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Status"), "status"],
        [msg("Last applied"), "last_applied"],
        [msg("Enabled"), "enabled"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
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

    protected override renderExpanded(item: BlueprintInstance): SlottedTemplateResult {
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

    protected override row(item: BlueprintInstance): SlottedTemplateResult[] {
        const description = formatBlueprintDescription(item);

        return [
            html`<div>${item.name}</div>
                ${description
                    ? html`<small><ak-mdx .content=${description}></ak-mdx></small>`
                    : nothing}`,
            BlueprintStatus(item),
            Timestamp(item.lastApplied),
            html`<ak-status-label ?good=${item.enabled}></ak-status-label>`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(BlueprintForm, item.pk, item.name)}
                ${IconPermissionButton(item.name, {
                    model: ModelEnum.AuthentikBlueprintsBlueprintinstance,
                    objectPk: item.pk,
                })}

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

    protected override renderObjectCreate(): SlottedTemplateResult {
        return guard([], () => {
            return [
                ModalInvokerButton(BlueprintForm),
                html`<button
                    class="pf-c-button pf-m-primary"
                    type="button"
                    ${modalInvoker(() => {
                        return html`<ak-blueprint-import-form>
                            <a
                                target="_blank"
                                rel="noopener noreferrer"
                                href=${docLink("/customize/blueprints/working_with_blueprints/")}
                                slot="read-more-link"
                                >${msg("Flow Examples")}</a
                            >
                            <span slot="banner-warning">
                                ${msg(
                                    "Warning: Blueprint files may contain objects such as users, policies and expression.",
                                )}<br />${msg(
                                    "You should only import files from trusted sources and review blueprints before importing them.",
                                )}
                            </span>
                        </ak-blueprint-import-form>`;
                    })}
                >
                    ${msg("Import")}
                </button>`,
            ];
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-blueprint-list": BlueprintListPage;
    }
}
