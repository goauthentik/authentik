import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { Flow, FlowsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

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
        return gettext("pf-icon pf-icon-process-automation");
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
            html`${item.stages?.size}`,
            html`${item.policies?.size}`,
            html`
            <ak-modal-button href="${AdminURLManager.flows(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${AdminURLManager.flows(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <a class="pf-c-button pf-m-secondary ak-root-link" href="${AdminURLManager.flows(`${item.pk}/execute/?next=/%23${window.location.href}`)}">
                ${gettext("Execute")}
            </a>
            <a class="pf-c-button pf-m-secondary ak-root-link" href="${AdminURLManager.flows(`${item.pk}/export/`)}">
                ${gettext("Export")}
            </a>
            `,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${AdminURLManager.flows("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        <ak-modal-button href=${AdminURLManager.flows("import/")}>
            <ak-spinner-button slot="trigger" class="pf-m-secondary">
                ${gettext("Import")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
