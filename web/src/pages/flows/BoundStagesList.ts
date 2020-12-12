import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { PBResponse } from "../../api/client";
import { Table } from "../../elements/table/Table";

import "../../elements/Tabs";
import "../../elements/AdminLoginsChart";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { FlowStageBinding } from "../../api/flow";

@customElement("ak-bound-stages-list")
export class BoundStagesList extends Table<FlowStageBinding> {
    expandable = true;

    @property()
    target?: string;

    apiEndpoint(page: number): Promise<PBResponse<FlowStageBinding>> {
        return FlowStageBinding.list({
            target: this.target || "",
            ordering: "order",
            page: page,
        });
    }

    columns(): string[] {
        return ["Order", "Name", "Type", ""];
    }

    row(item: FlowStageBinding): TemplateResult[] {
        return [
            html`${item.order}`,
            html`${item.stage_obj.name}`,
            html`${item.stage_obj.verbose_name}`,
            html`
            <ak-modal-button href="administration/stages/bindings/${item.pk}/update/">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    Edit
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="administration/stages/bindings/${item.pk}/delete/">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    Delete
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }

    renderExpanded(item: FlowStageBinding): TemplateResult {
        return html`
        <td></td>
        <td role="cell">
            <div class="pf-c-table__expandable-row-content">
                <div class="pf-c-content">
                    <p>Git URL: <small>${item.stage_obj.name}</small> </p>
                    <p>Latest commit SHA1 <small>64ae92893d7a98c71b3ef56835ed1c96354526be</small> </p>
                    <p>Status <small>20 total files changed</small> </p>
                    <p>License <small>Apache License 2.9</small> </p>
                </div>
            </div>
        </td>
        <td></td>
        <td></td>`;
    }

    renderEmpty(): TemplateResult {
        const createUrl = `/administration/stages/bindings/create/?target=${this.target}`;
        return super.renderEmpty(html`<ak-empty-state header=${gettext("No Stages bound")} icon="pf-icon-module">
            <div slot="body">
                ${gettext("No stages are currently bound to this flow.")}
            </div>
            <div slot="primary">
                <ak-modal-button href=${createUrl}>
                    <ak-spinner-button slot="trigger" class="pf-m-primary">
                        ${gettext("Bind Stage")}
                    </ak-spinner-button>
                    <div slot="modal"></div>
                </ak-modal-button>
            </div>
        </ak-empty-state>`);
    }

    renderToolbar(): TemplateResult {
        const createUrl = `/administration/stages/bindings/create/?target=${this.target}`;
        return html`
        <ak-modal-button href=${createUrl}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Bind Stage")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
