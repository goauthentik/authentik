import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ConfirmationForm";
import "./FlowForm";
import "./FlowImportForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { Flow, FlowsApi } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "../../api/Config";

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

    apiEndpoint(page: number): Promise<AKResponse<Flow>> {
        return new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Identifier`, "slug"),
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Designation`, "designation"),
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
            html`<a href="#/flow/flows/${item.slug}">
                <code>${item.slug}</code>
            </a>`,
            html`${item.name}`,
            html`${item.designation}`,
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
                        new FlowsApi(DEFAULT_CONFIG)
                            .flowsInstancesExecuteRetrieve({
                                slug: item.slug,
                            })
                            .then((link) => {
                                window.location.assign(
                                    `${link.link}?next=/%23${window.location.href}`,
                                );
                            });
                    }}
                >
                    <i class="fas fa-play"></i>
                </button>
                <a class="pf-c-button pf-m-plain" href=${item.exportUrl}>
                    <i class="fas fa-download"></i>
                </a>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html` <ak-forms-modal>
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
            </ak-forms-confirm>`;
    }
}
