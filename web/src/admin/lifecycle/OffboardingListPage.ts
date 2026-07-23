import "#admin/lifecycle/LifecyclePreviewBanner";
import "#components/ak-status-label";
import "#components/ak-switch-input";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/timestamp/ak-timestamp";

import { aki } from "#common/api/client";
import { me } from "#common/users";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { offboardingActionLabel, OffboardingStatus } from "#admin/lifecycle/utils";

import { LifecycleApi, OffboardingStatusEnum, UserOffboarding } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-offboarding-list")
export class OffboardingListPage extends TablePage<UserOffboarding> {
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for an offboarding by username...");
    public override pageTitle = msg("User Offboardings");
    public override pageDescription = msg(
        "Scheduled deactivation or deletion of users, and their outcomes.",
    );
    public override pageIcon = "pf-icon pf-icon-user";

    @property()
    public override order = "scheduled_at";

    protected override searchEnabled = true;

    @state()
    showOnlyPending = true;

    @state()
    protected currentUserPk?: number;

    public connectedCallback(): void {
        super.connectedCallback();
        me().then((session) => {
            this.currentUserPk = session.user.pk;
        });
    }

    // Shared by the bulk and per-row cancel paths so they stay in sync.
    #cancelOffboarding = (item: UserOffboarding) =>
        aki(LifecycleApi).lifecycleUserOffboardingDestroy({ id: item.id });

    #cancelMetadata = (item: UserOffboarding) => [
        { key: msg("User"), value: item.userObj.username },
        { key: msg("Action"), value: offboardingActionLabel(item.action) },
    ];

    protected async apiEndpoint(): Promise<PaginatedResponse<UserOffboarding>> {
        return aki(LifecycleApi).lifecycleUserOffboardingList({
            ...(await this.defaultEndpointConfig()),
            status: this.showOnlyPending ? OffboardingStatusEnum.Pending : undefined,
        });
    }

    protected override renderSectionBefore(): SlottedTemplateResult {
        return html`<ak-lifecycle-preview-banner></ak-lifecycle-preview-banner>`;
    }

    protected override renderToolbar(): TemplateResult {
        return html`
            <ak-switch-input
                name="showOnlyPending"
                ?checked=${this.showOnlyPending}
                label=${msg("Only show pending offboardings")}
                @change=${() => {
                    this.showOnlyPending = !this.showOnlyPending;
                    this.page = 1;
                    this.fetch();
                }}
            >
            </ak-switch-input>
            ${super.renderToolbar()}
        `;
    }

    protected override columns: TableColumn[] = [
        [msg("User"), "user__username"],
        [msg("Action"), "action"],
        [msg("Scheduled for"), "scheduled_at"],
        [msg("Status"), "status"],
        [msg("Scheduled by")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Offboarding(s)")}
            action=${msg("canceled")}
            button-label=${msg("Cancel Offboardings")}
            .objects=${this.selectedElements}
            .delete=${this.#cancelOffboarding}
            .metadata=${this.#cancelMetadata}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Cancel Offboardings")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected renderRowActions(item: UserOffboarding): SlottedTemplateResult {
        // Only a pending offboarding can be cancelled, and never your own — the
        // backend enforces both, so hide the control rather than offer a dead 403.
        const cancelable =
            item.status === OffboardingStatusEnum.Pending && item.user !== this.currentUserPk;
        if (!cancelable) {
            return html`${msg("-")}`;
        }
        return html`<ak-forms-delete-bulk
            object-label=${msg("Offboarding(s)")}
            action=${msg("canceled")}
            button-label=${msg("Cancel Offboarding")}
            .objects=${[item]}
            .delete=${this.#cancelOffboarding}
            .metadata=${this.#cancelMetadata}
        >
            <button slot="trigger" class="pf-c-button pf-m-secondary">${msg("Cancel")}</button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: UserOffboarding): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.user}">${item.userObj.username}</a>`,
            offboardingActionLabel(item.action),
            html`<ak-timestamp .timestamp=${item.scheduledAt} datetime></ak-timestamp>`,
            OffboardingStatus({ status: item.status }),
            item.createdByObj?.username ?? msg("-"),
            this.renderRowActions(item),
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-offboarding-list": OffboardingListPage;
    }
}
