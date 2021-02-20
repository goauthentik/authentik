import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { Group } from "../../api/Groups";

@customElement("ak-group-list")
export class GroupListPage extends TablePage<Group> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Groups");
    }
    pageDescription(): string {
        return gettext("Group users together and give them permissions based on the membership.");
    }
    pageIcon(): string {
        return gettext("pf-icon pf-icon-users");
    }

    @property()
    order = "slug";

    apiEndpoint(page: number): Promise<AKResponse<Group>> {
        return Group.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Parent", "parent"),
            new TableColumn("Members"),
            new TableColumn("Superuser privileges?"),
            new TableColumn(""),
        ];
    }

    row(item: Group): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.parent || "-"}`,
            html`${item.users.length}`,
            html`${item.is_superuser ? "Yes" : "No"}`,
            html`
            <ak-modal-button href="${Group.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${Group.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${Group.adminUrl("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
