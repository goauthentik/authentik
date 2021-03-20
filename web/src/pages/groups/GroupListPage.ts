import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/forms/DeleteForm";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, Group } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { AdminURLManager } from "../../api/legacy";

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
        return "pf-icon pf-icon-users";
    }

    @property()
    order = "slug";

    apiEndpoint(page: number): Promise<AKResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
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
            html`${item.users.keys.length}`,
            html`${item.isSuperuser ? "Yes" : "No"}`,
            html`
            <ak-modal-button href="${AdminURLManager.groups(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Group")}
                .delete=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreGroupsDelete({
                        groupUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-modal-button href=${AdminURLManager.groups("create/")}>
            <ak-spinner-button slot="trigger" class="pf-m-primary">
                ${gettext("Create")}
            </ak-spinner-button>
            <div slot="modal"></div>
        </ak-modal-button>
        ${super.renderToolbar()}
        `;
    }
}
