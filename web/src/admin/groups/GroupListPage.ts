import "#admin/groups/GroupForm";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { GroupForm } from "#admin/groups/GroupForm";

import { CoreApi, Group } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-group-list")
export class GroupListPage extends TablePage<Group> {
    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;

    public searchPlaceholder = msg("Search for a group by name…");
    public searchLabel = msg("Group Search");
    public pageTitle = msg("Groups");
    public pageDescription = msg(
        "Group users together and give them permissions based on the membership.",
    );
    public pageIcon = "pf-icon pf-icon-users";
    public supportsQL = true;

    @property()
    public order = "name";

    protected async apiEndpoint(): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ...(await this.defaultEndpointConfig()),
            includeUsers: false,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Members")],
        [msg("Superuser privileges?")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    #openNewGroupModal = GroupForm.asModalInvoker();
    #openEditGroupModal = GroupForm.asEditModalInvoker();

    protected renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Group(s)")}
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

    protected row(item: Group): SlottedTemplateResult[] {
        return [
            html`<a
                href="#/identity/groups/${item.pk}"
                aria-label=${msg(str`View details of group "${item.name}"`)}
                >${item.name}</a
            >`,
            html`${Array.from(item.users || []).length}`,
            html`<ak-status-label type="neutral" ?good=${item.isSuperuser}></ak-status-label>`,
            html`<div>
                <button
                    class="pf-c-button pf-m-plain"
                    aria-label=${msg(str`Edit "${item.name}"`)}
                    data-pk=${item.pk}
                    @click=${this.#openEditGroupModal}
                >
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </div>`,
        ];
    }

    protected renderObjectCreate(): TemplateResult {
        return html`<button class="pf-c-button pf-m-primary" @click=${this.#openNewGroupModal}>
            ${msg("New Group")}
        </button>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-list": GroupListPage;
    }
}
