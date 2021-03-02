import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../../elements/table/Table";
import { PolicyBinding } from "../../api/PolicyBindings";

import "../../elements/Tabs";
import "../../elements/AdminLoginsChart";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/Dropdown";
import { Policy } from "../../api/Policies";
import { until } from "lit-html/directives/until";
import { PAGE_SIZE } from "../../constants";

@customElement("ak-bound-policies-list")
export class BoundPoliciesList extends Table<PolicyBinding> {
    @property()
    target?: string;

    apiEndpoint(page: number): Promise<AKResponse<PolicyBinding>> {
        return PolicyBinding.list({
            target: this.target || "",
            ordering: "order",
            page: page,
            page_size: PAGE_SIZE,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Policy / User / Group"),
            new TableColumn("Enabled", "enabled"),
            new TableColumn("Order", "order"),
            new TableColumn("Timeout", "timeout"),
            new TableColumn(""),
        ];
    }

    getPolicyUserGroupRow(item: PolicyBinding): string {
        if (item.policy) {
            return gettext(`Policy ${item.policy.name}`);
        } else if (item.group) {
            return gettext(`Group ${item.group.name}`);
        } else if (item.user) {
            return gettext(`User ${item.user.name}`);
        } else {
            return gettext("");
        }
    }

    row(item: PolicyBinding): TemplateResult[] {
        return [
            html`${this.getPolicyUserGroupRow(item)}`,
            html`${item.enabled ? "Yes" : "No"}`,
            html`${item.order}`,
            html`${item.timeout}`,
            html`
            <ak-modal-button href="${PolicyBinding.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${PolicyBinding.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
        ];
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(html`<ak-empty-state header=${gettext("No Policies bound.")} icon="pf-icon-module">
            <div slot="body">
                ${gettext("No policies are currently bound to this object.")}
            </div>
            <div slot="primary">
                <ak-modal-button href=${PolicyBinding.adminUrl(`create/?target=${this.target}`)}>
                    <ak-spinner-button slot="trigger" class="pf-m-primary">
                        ${gettext("Bind Policy")}
                    </ak-spinner-button>
                    <div slot="modal"></div>
                </ak-modal-button>
            </div>
        </ak-empty-state>`);
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-dropdown class="pf-c-dropdown">
            <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                <span class="pf-c-dropdown__toggle-text">${gettext("Create Policy")}</span>
                <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
            </button>
            <ul class="pf-c-dropdown__menu" hidden>
                ${until(Policy.getTypes().then((types) => {
                    return types.map((type) => {
                        return html`<li>
                            <ak-modal-button href="${type.link}">
                                <button slot="trigger" class="pf-c-dropdown__menu-item">${type.name}<br>
                                    <small>${type.description}</small>
                                </button>
                                <div slot="modal"></div>
                            </ak-modal-button>
                        </li>`;
                    });
                }), html`<ak-spinner></ak-spinner>`)}
            </ul>
        </ak-dropdown>
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
