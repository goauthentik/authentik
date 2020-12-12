import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { PBResponse } from "../../api/client";
import { PolicyBinding } from "../../api/policy_binding";
import { Table } from "../../elements/table/Table";

import "../../elements/Tabs";
import "../../elements/AdminLoginsChart";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";

@customElement("ak-bound-policies-list")
export class BoundPoliciesList extends Table<PolicyBinding> {
    @property()
    target?: string;

    apiEndpoint(page: number): Promise<PBResponse<PolicyBinding>> {
        return PolicyBinding.list({
            target: this.target || "",
            ordering: "order",
            page: page,
        });
    }

    columns(): string[] {
        return ["Policy", "Enabled", "Order", "Timeout", ""];
    }

    row(item: PolicyBinding): TemplateResult[] {
        return [
            html`${item.policy_obj.name}`,
            html`${item.enabled ? "Yes" : "No"}`,
            html`${item.order}`,
            html`${item.timeout}`,
            html`
            <ak-modal-button href="${PolicyBinding.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    Edit
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${PolicyBinding.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    Delete
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${PolicyBinding.adminUrl(`create/?target=${this.target}`)}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Bind Policy")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
