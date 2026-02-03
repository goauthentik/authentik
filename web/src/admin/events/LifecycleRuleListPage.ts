import "#admin/events/LifecycleRuleForm";
import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import {DEFAULT_CONFIG} from "#common/api/config";

import {PaginatedResponse, TableColumn} from "#elements/table/Table";
import {TablePage} from "#elements/table/TablePage";
import {SlottedTemplateResult} from "#elements/types";

import {
    LifecycleRule,
    RbacPermissionsAssignedByRolesListModelEnum, ReviewsApi,
} from "@goauthentik/api";

import {msg} from "@lit/localize";
import {html, TemplateResult} from "lit";
import {customElement, property} from "lit/decorators.js";

@customElement("ak-lifecycle-rule-list")
export class LifecycleRuleListPage extends TablePage<LifecycleRule> {
    expandable = false;
    checkbox = true;
    clearOnRefresh = true;

    protected override searchEnabled = true;
    public pageTitle = msg("Object Lifecycle Rules");
    public pageDescription = msg(
        "Schedule periodic access reviews for objects in authentik.",
    );
    public pageIcon = "pf-icon pf-icon-history";

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<LifecycleRule>> {
        return new ReviewsApi(DEFAULT_CONFIG).reviewsLifecycleRulesList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        [msg("Target"), "content_type__model"],
        [msg("Frequency (months)"), "interval_months"],
        [msg("Grace period (days)"), "grace_period_days"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`
            <ak-forms-delete-bulk
                objectLabel=${msg("Lifecycle rule(s)")}
                .objects=${this.selectedElements}
                .delete=${(item: LifecycleRule) => {
                    if (item.id)
                        return new ReviewsApi(DEFAULT_CONFIG).reviewsLifecycleRulesDestroy({
                            id: item.id,
                        });
                }}
                .metadata=${(item: LifecycleRule) =>
                    [{key: msg("Target"), value: item.targetVerbose}]}
            >
                <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                    ${msg("Delete")}
                </button>
            </ak-forms-delete-bulk>`;
    }

    row(item: LifecycleRule): SlottedTemplateResult[] {
        return [
            html`${item.targetVerbose}`,
            html`${item.intervalMonths}`,
            html`${item.gracePeriodDays}`,
            html`
                <div>
                    <ak-forms-modal>
                        <span slot="submit">${msg("Update")}</span>
                        <span slot="header">${msg("Update Lifecycle Rule")}</span>
                        <ak-lifecycle-rule-form slot="form"
                                                .instancePk=${item.id}></ak-lifecycle-rule-form>
                        <button slot="trigger" class="pf-c-button pf-m-plain">
                            <pf-tooltip position="top" content=${msg("Edit")}>
                                <i class="fas fa-edit" aria-hidden="true"></i>
                            </pf-tooltip>
                        </button>
                    </ak-forms-modal>

                    <ak-rbac-object-permission-modal
                        model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikReviewsLifecyclerule}
                        objectPk=${item.id}
                    >
                    </ak-rbac-object-permission-modal>
                </div>`,
        ];
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
