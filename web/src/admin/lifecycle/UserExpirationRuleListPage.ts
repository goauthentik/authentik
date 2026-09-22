import "#admin/lifecycle/LifecyclePreviewBanner";
import "#admin/lifecycle/UserExpirationRuleForm";
import "#admin/lifecycle/UserExpirationRulePreview";
import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { UserExpirationRuleForm } from "#admin/lifecycle/UserExpirationRuleForm";
import { offboardingActionLabel } from "#admin/lifecycle/utils";

import { LifecycleApi, ModelEnum, UserExpirationRule } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-expiration-rule-list")
export class UserExpirationRuleListPage extends TablePage<UserExpirationRule> {
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override expandable = true;

    public override searchPlaceholder = msg("Search for an expiration rule by name...", {
        id: "user-expiration.list.search-placeholder",
    });

    public override pageTitle = msg("User Expiration Rules", {
        id: "user-expiration.list.title",
    });

    public override pageDescription = msg(
        "Automatically deactivate or delete users who have not signed in for a configurable period.",
        { id: "user-expiration.list.description" },
    );

    public override pageIcon = "pf-icon pf-icon-user";

    public override order = "name";

    protected override searchEnabled = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<UserExpirationRule>> {
        return aki(LifecycleApi).lifecycleUserExpirationRulesList(
            await this.defaultEndpointConfig(),
        );
    }

    protected override renderSectionBefore(): SlottedTemplateResult {
        return html`<ak-lifecycle-preview-banner></ak-lifecycle-preview-banner>`;
    }

    protected override columns: TableColumn[] = [
        [msg("Name", { id: "user-expiration.field.name.label" }), "name"],
        [msg("Enabled", { id: "user-expiration.field.enabled.label" }), "enabled"],
        [msg("Applies to", { id: "user-expiration.column.applies-to" })],
        [
            msg("Inactivity duration", {
                id: "user-expiration.field.inactivity-duration.label",
            }),
        ],
        [msg("Action", { id: "offboarding.field.action.label" }), "action"],
        [msg("Actions", { id: "common.table.actions" }), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Expiration rule(s)", { id: "user-expiration.object-label" })}
            .objects=${this.selectedElements}
            .usedBy=${(item: UserExpirationRule) =>
                aki(LifecycleApi).lifecycleUserExpirationRulesUsedByList({ id: item.pk! })}
            .delete=${(item: UserExpirationRule) =>
                aki(LifecycleApi).lifecycleUserExpirationRulesDestroy({ id: item.pk! })}
            .metadata=${(item: UserExpirationRule) => [
                {
                    key: msg("Action", { id: "offboarding.field.action.label" }),
                    value: offboardingActionLabel(item.action),
                },
            ]}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete", { id: "common.actions.delete" })}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: UserExpirationRule): SlottedTemplateResult[] {
        return [
            item.name,
            html`<ak-status-label .good=${item.enabled ?? false}></ak-status-label>`,
            item.groupObj?.name ?? msg("All users", { id: "user-expiration.scope.all-users" }),
            item.inactivityDuration || msg("-"),
            offboardingActionLabel(item.action),
            html`<div class="ak-c-table__actions">
                ${IconEditButton(UserExpirationRuleForm, item.pk ?? null, item.name)}

                <ak-user-expiration-rule-preview .rule=${item}>
                    <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                        ${msg("Preview", { id: "user-expiration.preview.trigger" })}
                    </button>
                </ak-user-expiration-rule-preview>

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikLifecycleUserexpirationrule}
                    objectPk=${item.pk!}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderExpanded(item: UserExpirationRule): SlottedTemplateResult {
        return html`<div class="pf-c-content">
            <ak-bound-policies-list
                .target=${item.pbmUuid}
                .policyEngineMode=${item.policyEngineMode}
            >
                <span slot="description"
                    >${msg(
                        "Users must pass these policies to be expired. With no bindings, every user in scope is expired.",
                        { id: "user-expiration.policies.description" },
                    )}</span
                >
            </ak-bound-policies-list>
        </div>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(UserExpirationRuleForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-expiration-rule-list": UserExpirationRuleListPage;
    }
}
