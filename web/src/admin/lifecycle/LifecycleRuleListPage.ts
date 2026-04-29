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

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { LifecycleRuleForm } from "#admin/lifecycle/LifecycleRuleForm";

import { LifecycleApi, LifecycleRule, ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-lifecycle-rule-list")
export class LifecycleRuleListPage extends TablePage<LifecycleRule> {
    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for a lifecycle rule by name or target...");
    public override pageTitle = msg("Object Lifecycle Rules");
    public override pageDescription = msg("Schedule periodic reviews for objects in authentik.");
    public override pageIcon = "pf-icon pf-icon-history";

    public override order = "name";

    protected override searchEnabled = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<LifecycleRule>> {
        return new LifecycleApi(DEFAULT_CONFIG).lifecycleRulesList(
            await this.defaultEndpointConfig(),
        );
    }

    protected override renderSectionBefore(): SlottedTemplateResult {
        return html`<ak-lifecycle-preview-banner></ak-lifecycle-preview-banner>`;
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Target"), "content_type__model"],
        [msg("Interval"), "interval"],
        [msg("Grace period"), "grace_period"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
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

    protected override row(item: LifecycleRule): SlottedTemplateResult[] {
        return [
            item.name,
            item.targetVerbose,
            item.interval || msg("-"),
            item.gracePeriod || msg("-"),
            html`<div class="ak-c-table__actions">
                ${IconEditButton(LifecycleRuleForm, item.id, item.name)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikLifecycleLifecyclerule}
                    objectPk=${item.id}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderExpanded(item: LifecycleRule): SlottedTemplateResult {
        const [appLabel, modelName] = ModelEnum.AuthentikLifecycleLifecyclerule.split(".");
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Tasks")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <ak-task-list
                            search-placeholder=${msg("Search tasks...")}
                            .relObjAppLabel=${appLabel}
                            .relObjModel=${modelName}
                            .relObjId="${item.id}"
                        ></ak-task-list>
                    </div>
                </dd>
            </div>
        </dl>`;
    }
    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(LifecycleRuleForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-lifecycle-rule-list": LifecycleRuleListPage;
    }
}
