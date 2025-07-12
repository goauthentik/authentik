import "#admin/groups/GroupForm";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";

import { CoreApi, Group } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-group-list")
export class GroupListPage extends TablePage<Group> {
    checkbox = true;
    clearOnRefresh = true;
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Groups");
    }
    pageDescription(): string {
        return msg("Group users together and give them permissions based on the membership.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-users";
    }

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ...(await this.defaultEndpointConfig()),
            includeUsers: false,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Parent"), "parent"),
            new TableColumn(msg("Members")),
            new TableColumn(msg("Superuser privileges?")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Group(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Group) => {
                return new CoreApi(DEFAULT_CONFIG).coreGroupsUsedByList({
                    groupUuid: item.pk,
                });
            }}
            .delete=${(item: Group) => {
                return new CoreApi(DEFAULT_CONFIG).coreGroupsDestroy({
                    groupUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Group): TemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.pk}">${item.name}</a>`,
            html`${item.parentName || msg("-")}`,
            html`${Array.from(item.users || []).length}`,
            html`<ak-status-label type="info" ?good=${item.isSuperuser}></ak-status-label>`,
            html`<ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update Group")} </span>
                <ak-group-form slot="form" .instancePk=${item.pk}> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Group")} </span>
                <ak-group-form slot="form"> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-list": GroupListPage;
    }
}
