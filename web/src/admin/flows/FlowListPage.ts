import "@goauthentik/admin/flows/FlowForm";
import "@goauthentik/admin/flows/FlowImportForm";
import { DesignationToLabel } from "@goauthentik/admin/flows/utils";
import { AndNext, DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { groupBy } from "@goauthentik/common/utils";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ConfirmationForm";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Flow, FlowsApi } from "@goauthentik/api";

@customElement("ak-flow-list")
export class FlowListPage extends TablePage<Flow> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Flows");
    }
    pageDescription(): string {
        return msg(
            "Flows describe a chain of Stages to authenticate, enroll or recover a user. Stages are chosen based on policies applied to them.",
        );
    }
    pageIcon(): string {
        return "pf-icon pf-icon-process-automation";
    }

    checkbox = true;

    @property()
    order = "slug";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Flow>> {
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    groupBy(items: Flow[]): [string, Flow[]][] {
        return groupBy(items, (flow) => {
            return DesignationToLabel(flow.designation);
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Identifier"), "slug"),
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Stages")),
            new TableColumn(msg("Policies")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Flow(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Flow) => {
                return new FlowsApi(DEFAULT_CONFIG).flowsInstancesUsedByList({
                    slug: item.slug,
                });
            }}
            .delete=${(item: Flow) => {
                return new FlowsApi(DEFAULT_CONFIG).flowsInstancesDestroy({
                    slug: item.slug,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Flow): TemplateResult[] {
        return [
            html`<div>
                    <a href="#/flow/flows/${item.slug}">
                        <code>${item.slug}</code>
                    </a>
                </div>
                <small>${item.title}</small>`,
            html`${item.name}`,
            html`${Array.from(item.stages || []).length}`,
            html`${Array.from(item.policies || []).length}`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Flow")} </span>
                    <ak-flow-form slot="form" .instancePk=${item.slug}> </ak-flow-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                <button
                    class="pf-c-button pf-m-plain"
                    @click=${() => {
                        const finalURL = `${window.location.origin}/if/flow/${item.slug}/${AndNext(
                            `${window.location.pathname}#${window.location.hash}`,
                        )}`;
                        window.open(finalURL, "_blank");
                    }}
                >
                    <i class="fas fa-play"></i>
                </button>
                <a class="pf-c-button pf-m-plain" href=${item.exportUrl}>
                    <i class="fas fa-download"></i>
                </a>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Flow")} </span>
                <ak-flow-form slot="form"> </ak-flow-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
            <ak-forms-modal>
                <span slot="submit"> ${msg("Import")} </span>
                <span slot="header"> ${msg("Import Flow")} </span>
                <ak-flow-import-form slot="form"> </ak-flow-import-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Import")}</button>
            </ak-forms-modal>
        `;
    }

    renderToolbar(): TemplateResult {
        return html`
            ${super.renderToolbar()}
            <ak-forms-confirm
                successMessage=${msg("Successfully cleared flow cache")}
                errorMessage=${msg("Failed to delete flow cache")}
                action=${msg("Clear cache")}
                .onConfirm=${() => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsInstancesCacheClearCreate();
                }}
            >
                <span slot="header"> ${msg("Clear Flow cache")} </span>
                <p slot="body">
                    ${msg(
                        `Are you sure you want to clear the flow cache?
            This will cause all flows to be re-evaluated on their next usage.`,
                    )}
                </p>
                <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                    ${msg("Clear cache")}
                </button>
                <div slot="modal"></div>
            </ak-forms-confirm>
        `;
    }
}
