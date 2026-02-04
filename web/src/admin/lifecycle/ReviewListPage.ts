import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#admin/lifecycle/AccessReviewStastus";
import "#admin/lifecycle/LifecyclePreviewBanner";
import "#components/ak-switch-input";

import {DEFAULT_CONFIG} from "#common/api/config";

import {PaginatedResponse, TableColumn} from "#elements/table/Table";
import {TablePage} from "#elements/table/TablePage";
import {SlottedTemplateResult} from "#elements/types";

import {
    Review, LifecycleApi,
} from "@goauthentik/api";

import {msg} from "@lit/localize";
import {html, TemplateResult} from "lit";
import {customElement, property, state} from "lit/decorators.js";

@customElement("ak-review-list")
export class ReviewListPage extends TablePage<Review> {
    expandable = false;
    checkbox = false;
    clearOnRefresh = true;

    protected override searchEnabled = false;
    public pageTitle = msg("Open Access Reviews");
    public pageDescription = msg(
        "See all currently open access reviews.",
    );
    public pageIcon = "pf-icon pf-icon-history";

    @property()
    order = "grace_period_till";

    @state()
    showOnlyMine = false;

    async apiEndpoint(): Promise<PaginatedResponse<Review>> {
        return new LifecycleApi(DEFAULT_CONFIG).lifecycleReviewsListOpen({
            ...await this.defaultEndpointConfig(),
            userIsReviewer: this.showOnlyMine || undefined,
        },);
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
                @change=${(ev: Event) => {this.showOnlyMine = !this.showOnlyMine; this.fetch();}}
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

    row(item: Review): SlottedTemplateResult[] {
        return [
            html`<ak-access-review-status status=${item.state}></ak-access-review-status>`,
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
