import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Flow, FlowsApi } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { AndNext, DEFAULT_CONFIG } from "../../api/Config";
import { uiConfig } from "../../common/config";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/ConfirmationForm";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import { groupBy } from "../../utils";
import "./FlowForm";
import "./FlowImportForm";
import { DesignationToLabel } from "./utils";

@customElement("ak-flow-list")
export class FlowListPage extends TablePage<Flow> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Flows`;
    }
    pageDescription(): string {
        return t`Flows describe a chain of Stages to authenticate, enroll or recover a user. Stages are chosen based on policies applied to them.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-process-automation";
    }

    checkbox = true;

    @property()
    order = "slug";

    async apiEndpoint(page: number): Promise<AKResponse<Flow>> {
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    groupBy(items: Flow[]): [string, Flow[]][] {
        return groupBy(items, (flow) => {
            if (!flow.designation) {
                return "";
            }
            return DesignationToLabel(flow.designation);
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Identifier`, "slug"),
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Stages`),
            new TableColumn(t`Policies`),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Flow(s)`}
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
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Flow): TemplateResult[] {
        return [
            html`<div>
                <div>
                    <a href="#/flow/flows/${item.slug}">
                        <code>${item.slug}</code>
                    </a>
                </div>
                <small>${item.title}</small>
            </div>`,
            html`${item.name}`,
            html`${Array.from(item.stages || []).length}`,
            html`${Array.from(item.policies || []).length}`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Flow`} </span>
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
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Flow`} </span>
                <ak-flow-form slot="form"> </ak-flow-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            <ak-forms-modal>
                <span slot="submit"> ${t`Import`} </span>
                <span slot="header"> ${t`Import Flow`} </span>
                <ak-flow-import-form slot="form"> </ak-flow-import-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Import`}</button>
            </ak-forms-modal>
        `;
    }

    renderToolbar(): TemplateResult {
        return html`
            ${super.renderToolbar()}
            <ak-forms-confirm
                successMessage=${t`Successfully cleared flow cache`}
                errorMessage=${t`Failed to delete flow cache`}
                action=${t`Clear cache`}
                .onConfirm=${() => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsInstancesCacheClearCreate();
                }}
            >
                <span slot="header"> ${t`Clear Flow cache`} </span>
                <p slot="body">
                    ${t`Are you sure you want to clear the flow cache?
                    This will cause all flows to be re-evaluated on their next usage.`}
                </p>
                <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                    ${t`Clear cache`}
                </button>
                <div slot="modal"></div>
            </ak-forms-confirm>
        `;
    }
}
