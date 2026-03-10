import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#admin/lifecycle/LifecyclePreviewBanner";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { LifecycleIterationStatus } from "#admin/lifecycle/utils";

import { LifecycleApi, LifecycleIteration } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-review-list")
export class ReviewListPage extends TablePage<LifecycleIteration> {
    expandable = false;
    checkbox = false;
    clearOnRefresh = true;

    protected override searchEnabled = false;
    public pageTitle = msg("Open Reviews");
    public pageDescription = msg("See all currently open reviews.");
    public pageIcon = "pf-icon pf-icon-history";

    @property()
    order = "grace_period_till";

    @state()
    showOnlyMine = false;

    async apiEndpoint(): Promise<PaginatedResponse<LifecycleIteration>> {
        return new LifecycleApi(DEFAULT_CONFIG).lifecycleIterationsListOpen({
            ...(await this.defaultEndpointConfig()),
            userIsReviewer: this.showOnlyMine || undefined,
        });
    }

    protected renderSectionBefore?(): TemplateResult {
        return html`<ak-lifecycle-preview-banner></ak-lifecycle-preview-banner>`;
    }

    protected renderToolbar(): TemplateResult {
        return html`
            <ak-switch-input
                name="showOnlyMine"
                ?checked=${this.showOnlyMine}
                label=${msg("Only show reviews where I am a reviewer")}
                @change=${() => {
                    this.showOnlyMine = !this.showOnlyMine;
                    this.fetch();
                }}
            >
            </ak-switch-input>
            ${super.renderToolbar()}
        `;
    }

    protected columns: TableColumn[] = [
        [msg("State"), "state"],
        [msg("Object"), "content_type__model"],
        [msg("Opened"), "opened_on"],
        [msg("Grace period ends")],
    ];

    row(item: LifecycleIteration): SlottedTemplateResult[] {
        return [
            LifecycleIterationStatus({ status: item.state }),
            html`<a href="#${item.objectAdminUrl}">${item.objectVerbose}</a>`,
            html`<ak-timestamp .timestamp=${item.openedOn} datetime dateonly></ak-timestamp>`,
            html`<ak-timestamp .timestamp=${item.gracePeriodEnd} datetime dateonly></ak-timestamp>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-review-list": ReviewListPage;
    }
}
