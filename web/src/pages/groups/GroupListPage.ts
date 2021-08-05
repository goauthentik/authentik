import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/forms/DeleteForm";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, Group } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/ModalForm";
import "./GroupForm";

@customElement("ak-group-list")
export class GroupListPage extends TablePage<Group> {
    checkbox = true;
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Groups`;
    }
    pageDescription(): string {
        return t`Group users together and give them permissions based on the membership.`;
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
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Parent`, "parent"),
            new TableColumn(t`Members`),
            new TableColumn(t`Superuser privileges?`),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length !== 1;
        const item = this.selectedElements[0];
        return html`<ak-forms-delete
            .obj=${item}
            objectLabel=${t`Group`}
            .usedBy=${() => {
                return new CoreApi(DEFAULT_CONFIG).coreGroupsUsedByList({
                    groupUuid: item.pk,
                });
            }}
            .delete=${() => {
                return new CoreApi(DEFAULT_CONFIG).coreGroupsDestroy({
                    groupUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete>`;
    }

    row(item: Group): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.parent || "-"}`,
            html`${Array.from(item.users || []).length}`,
            html`${item.isSuperuser ? t`Yes` : t`No`}`,
            html` <ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update Group`} </span>
                <ak-group-form slot="form" .instancePk=${item.pk}> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Group`} </span>
                <ak-group-form slot="form"> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}
