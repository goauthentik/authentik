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

    row(item: FlowStageBinding): string[] {
        return [
            item.order.toString(),
            item.stage_obj.name,
            item.stage_obj.verbose_name,
            `
            <ak-modal-button href="administration/policies/bindings/${item.pk}/update/">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    Edit
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="administration/policies/bindings/${item.pk}/delete/">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    Delete
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }

    renderToolbar(): TemplateResult {
        const createUrl = `/administration/policies/bindings/create/?target=${this.target}`;
        return html`
        <ak-modal-button href=${createUrl}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
