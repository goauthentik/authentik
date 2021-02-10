import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../../elements/table/Table";

import "../../elements/Tabs";
import "../../elements/AdminLoginsChart";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/policies/BoundPoliciesList";
import { FlowStageBinding } from "../../api/Flows";

@customElement("ak-bound-stages-list")
export class BoundStagesList extends Table<FlowStageBinding> {
    expandable = true;

    @property()
    target?: string;

    apiEndpoint(page: number): Promise<AKResponse<FlowStageBinding>> {
        return FlowStageBinding.list({
            target: this.target || "",
            ordering: "order",
            page: page,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Order"),
            new TableColumn("Name"),
            new TableColumn("Type"),
            new TableColumn(""),
        ];
    }

    row(item: FlowStageBinding): TemplateResult[] {
        return [
            html`${item.order}`,
            html`${item.stage_obj.name}`,
            html`${item.stage_obj.verbose_name}`,
            html`
            <ak-modal-button href="${FlowStageBinding.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${FlowStageBinding.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }

    renderExpanded(item: FlowStageBinding): TemplateResult {
        return html`
        <td></td>
        <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <div class="pf-c-content">
                    <p>${gettext("These policies control when this stage will be applied to the flow.")}</p>
                    <ak-bound-policies-list .target=${item.policybindingmodel_ptr_id}>
                    </ak-bound-policies-list>
                </div>
            </div>
        </td>
        <td></td>
        <td></td>`;
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(html`<ak-empty-state header=${gettext("No Stages bound")} icon="pf-icon-module">
            <div slot="body">
                ${gettext("No stages are currently bound to this flow.")}
            </div>
            <div slot="primary">
                <ak-modal-button href="${FlowStageBinding.adminUrl(`create/?target=${this.target}`)}">
                    <ak-spinner-button slot="trigger" class="pf-m-primary">
                        ${gettext("Bind Stage")}
                    </ak-spinner-button>
                    <div slot="modal"></div>
                </ak-modal-button>
            </div>
        </ak-empty-state>`);
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href="${FlowStageBinding.adminUrl(`create/?target=${this.target}`)}">
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Bind Stage")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
