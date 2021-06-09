import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ConfirmationForm";
import "./FlowForm";
import "./FlowImportForm";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { Flow, FlowsApi } from "authentik-api";
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
            new TableColumn(""),
        ];
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
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update Flow`}
                </span>
                <ak-flow-form slot="form" .instancePk=${item.slug}>
                </ak-flow-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Edit`}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Flow`}
                .usedBy=${() => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsInstancesUsedByList({
                        slug: item.slug
                    });
                }}
                .delete=${() => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsInstancesDestroy({
                        slug: item.slug
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete`}
                </button>
            </ak-forms-delete>
            <button
                class="pf-c-button pf-m-secondary"
                @click=${() => {
                    new FlowsApi(DEFAULT_CONFIG).flowsInstancesExecuteRetrieve({
                        slug: item.slug
                    }).then(link => {
                        window.location.assign(`${link.link}?next=/%23${window.location.href}`);
                    });
                }}>
                ${t`Execute`}
            </button>
            <a class="pf-c-button pf-m-secondary" href="/api/v2beta/flows/instances/${item.slug}/export/">
                ${t`Export`}
            </a>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${t`Create`}
            </span>
            <span slot="header">
                ${t`Create Flow`}
            </span>
            <ak-flow-form slot="form">
            </ak-flow-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${t`Create`}
            </button>
        </ak-forms-modal>
        <ak-forms-modal>
            <span slot="submit">
                ${t`Import`}
            </span>
            <span slot="header">
                ${t`Import Flow`}
            </span>
            <ak-flow-import-form slot="form">
            </ak-flow-import-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${t`Import`}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        <ak-forms-confirm
            successMessage=${t`Successfully cleared flow cache`}
            errorMessage=${t`Failed to delete flow cache`}
            action=${t`Clear cache`}
            .onConfirm=${() => {
                return new FlowsApi(DEFAULT_CONFIG).flowsInstancesCacheClearCreate();
            }}>
            <span slot="header">
                ${t`Clear Flow cache`}
            </span>
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
