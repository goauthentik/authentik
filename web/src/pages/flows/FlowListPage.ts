import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { Flow } from "../../api/Flows";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";

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
        return Flow.list({
            ordering: this.order,
            page: page,
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
            html`<a href="#/flows/${item.slug}">
                <code>${item.slug}</code>
            </a>`,
            html`${item.name}`,
            html`${item.designation}`,
            html`${item.stages.length}`,
            html`${item.policies.length}`,
            html`
            <ak-modal-button href="${Flow.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Flow.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <a class="pf-c-button pf-m-secondary ak-root-link" href="${Flow.adminUrl(`${item.pk}/execute/?next=/%23${window.location.href}`)}">
                ${gettext("Execute")}
            </a>
            <a class="pf-c-button pf-m-secondary ak-root-link" href="${Flow.adminUrl(`${item.pk}/export/`)}">
                ${gettext("Export")}
            </a>
            `,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${Flow.adminUrl("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        <ak-modal-button href=${Flow.adminUrl("import/")}>
            <ak-spinner-button slot="trigger" class="pf-m-secondary">
                ${gettext("Import")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
