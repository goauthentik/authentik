import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteForm";
import "../../elements/forms/ModalForm";
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
        return gettext("Flows");
    }
    pageDescription(): string {
        return gettext("Flows describe a chain of Stages to authenticate, enroll or recover a user. Stages are chosen based on policies applied to them.");
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
            new TableColumn("Identifier", "slug"),
            new TableColumn("Name", "name"),
            new TableColumn("Designation", "designation"),
            new TableColumn("Stages"),
            new TableColumn("Policies"),
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
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext("Update Flow")}
                </span>
                <ak-flow-form slot="form" .flow=${item}>
                </ak-flow-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Flow")}
                .delete=${() => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsInstancesDelete({
                        slug: item.slug
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>
            <button
                class="pf-c-button pf-m-secondary ak-root-link"
                @click=${() => {
                    new FlowsApi(DEFAULT_CONFIG).flowsInstancesExecute({
                        slug: item.slug
                    }).then(link => {
                        window.location.assign(`${link.link}?next=/%23${window.location.href}`);
                    });
                }}>
                ${gettext("Execute")}
            </button>
            <a class="pf-c-button pf-m-secondary ak-root-link" href="${`${DEFAULT_CONFIG.basePath}/flows/instances/${item.slug}/export/`}">
                ${gettext("Export")}
            </a>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Create")}
            </span>
            <span slot="header">
                ${gettext("Create Flow")}
            </span>
            <ak-flow-form slot="form">
            </ak-flow-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Create")}
            </button>
        </ak-forms-modal>
        <ak-forms-modal>
            <span slot="submit">
                ${gettext("Import")}
            </span>
            <span slot="header">
                ${gettext("Import Flow")}
            </span>
            <ak-flow-import-form slot="form">
            </ak-flow-import-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${gettext("Import")}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
