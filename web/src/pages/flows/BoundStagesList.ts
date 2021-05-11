import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../../elements/table/Table";

import "../../elements/forms/DeleteForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ProxyForm";
import "./StageBindingForm";
import "../../elements/Tabs";
import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/Dropdown";
import "../policies/BoundPoliciesList";
import { until } from "lit-html/directives/until";
import { PAGE_SIZE } from "../../constants";
import { FlowsApi, FlowStageBinding, StagesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-bound-stages-list")
export class BoundStagesList extends Table<FlowStageBinding> {
    expandable = true;

    @property()
    target?: string;

    apiEndpoint(page: number): Promise<AKResponse<FlowStageBinding>> {
        return new FlowsApi(DEFAULT_CONFIG).flowsBindingsList({
            target: this.target || "",
            ordering: "order",
            page: page,
            pageSize: PAGE_SIZE,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Order`),
            new TableColumn(t`Name`),
            new TableColumn(t`Type`),
            new TableColumn(""),
        ];
    }

    row(item: FlowStageBinding): TemplateResult[] {
        return [
            html`${item.order}`,
            html`${item.stageObj?.name}`,
            html`${item.stageObj?.verboseName}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update ${item.stageObj?.verboseName}`}
                </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        "instancePk": item.stage
                    }}
                    type=${ifDefined(item.stageObj?.component)}>
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Edit Stage`}
                </button>
            </ak-forms-modal>
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update Stage binding`}
                </span>
                <ak-stage-binding-form slot="form" .instancePk=${item.pk}>
                </ak-stage-binding-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Edit Binding`}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Stage binding`}
                .delete=${() => {
                    return new FlowsApi(DEFAULT_CONFIG).flowsBindingsDelete({
                        fsbUuid: item.pk || "",
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete Binding`}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderExpanded(item: FlowStageBinding): TemplateResult {
        return html`
        <td></td>
        <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <div class="pf-c-content">
                    <p>${t`These bindings control if this stage will be applied to the flow.`}</p>
                    <ak-bound-policies-list .target=${item.policybindingmodelPtrId}>
                    </ak-bound-policies-list>
                </div>
            </div>
        </td>
        <td></td>
        <td></td>`;
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(html`<ak-empty-state header=${t`No Stages bound`} icon="pf-icon-module">
            <div slot="body">
                ${t`No stages are currently bound to this flow.`}
            </div>
            <div slot="primary">
                <ak-forms-modal>
                    <span slot="submit">
                        ${t`Create`}
                    </span>
                    <span slot="header">
                        ${t`Create Stage binding`}
                    </span>
                    <ak-stage-binding-form slot="form" targetPk=${ifDefined(this.target)}>
                    </ak-stage-binding-form>
                    <button slot="trigger" class="pf-c-button pf-m-primary">
                        ${t`Bind stage`}
                    </button>
                </ak-forms-modal>
            </div>
        </ak-empty-state>`);
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-dropdown class="pf-c-dropdown">
            <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                <span class="pf-c-dropdown__toggle-text">${t`Create Stage`}</span>
                <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
            </button>
            <ul class="pf-c-dropdown__menu" hidden>
                ${until(new StagesApi(DEFAULT_CONFIG).stagesAllTypes().then((types) => {
                    return types.map((type) => {
                        return html`<li>
                            <ak-forms-modal>
                                <span slot="submit">
                                    ${t`Create`}
                                </span>
                                <span slot="header">
                                    ${t`Create ${type.name}`}
                                </span>
                                <ak-proxy-form
                                    slot="form"
                                    type=${type.component}>
                                </ak-proxy-form>
                                <button slot="trigger" class="pf-c-dropdown__menu-item">
                                    ${type.name}<br>
                                    <small>${type.description}</small>
                                </button>
                            </ak-forms-modal>
                        </li>`;
                    });
                }), html`<ak-spinner></ak-spinner>`)}
            </ul>
        </ak-dropdown>
        <ak-forms-modal>
            <span slot="submit">
                ${t`Create`}
            </span>
            <span slot="header">
                ${t`Create Stage binding`}
            </span>
            <ak-stage-binding-form slot="form" targetPk=${ifDefined(this.target)}>
            </ak-stage-binding-form>
            <button slot="trigger" class="pf-c-button pf-m-secondary">
                ${t`Bind stage`}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
