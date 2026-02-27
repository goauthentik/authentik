import "#admin/lifecycle/LifecycleRuleForm";
import "#admin/lifecycle/LifecyclePreviewBanner";
import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import {
    LifecycleApi,
    LifecycleRule,
    ModelEnum,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-lifecycle-rule-list")
export class LifecycleRuleListPage extends TablePage<LifecycleRule> {
    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;

    public pageTitle = msg("Object Lifecycle Rules");
    public pageDescription = msg("Schedule periodic reviews for objects in authentik.");
    public pageIcon = "pf-icon pf-icon-history";

    public override order = "name";

    protected override searchEnabled = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<LifecycleRule>> {
        return new LifecycleApi(DEFAULT_CONFIG).lifecycleRulesList(
            await this.defaultEndpointConfig(),
        );
    }

    protected renderSectionBefore(): TemplateResult {
        return html`<ak-lifecycle-preview-banner></ak-lifecycle-preview-banner>`;
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Target"), "content_type__model"],
        [msg("Interval"), "interval"],
        [msg("Grace period"), "grace_period"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html` <ak-forms-delete-bulk
            object-label=${msg("Lifecycle rule(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: LifecycleRule) => {
                if (item.id)
                    return new LifecycleApi(DEFAULT_CONFIG).lifecycleRulesDestroy({
                        id: item.id,
                    });
            }}
            .metadata=${(item: LifecycleRule) => [
                { key: msg("Target"), value: item.targetVerbose },
            ]}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: LifecycleRule): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.targetVerbose}`,
            html`${item.interval}`,
            html`${item.gracePeriod}`,
            html` <div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Lifecycle Rule")}</span>
                    <ak-lifecycle-rule-form
                        slot="form"
                        .instancePk=${item.id}
                    ></ak-lifecycle-rule-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>

                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikLifecycleLifecyclerule}
                    objectPk=${item.id}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    renderExpanded(item: LifecycleRule): TemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikLifecycleLifecyclerule.split(".");
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Tasks")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <ak-task-list
                            .relObjAppLabel=${appLabel}
                            .relObjModel=${modelName}
                            .relObjId="${item.id}"
                        ></ak-task-list>
                    </div>
                </dd>
            </div>
        </dl>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Create")}</span>
                <span slot="header">${msg("Create Object Lifecycle Rule")}</span>
                <ak-lifecycle-rule-form slot="form"></ak-lifecycle-rule-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-lifecycle-rule-list": LifecycleRuleListPage;
    }
}
