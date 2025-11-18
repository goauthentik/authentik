import "#admin/groups/GroupForm";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EntityLabel } from "#common/i18n/nouns";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, Group } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-group-list")
export class GroupListPage extends TablePage<Group> {
    checkbox = true;
    clearOnRefresh = true;
    protected override searchEnabled = true;
    protected override entityLabel: EntityLabel = {
        singular: msg("Group", { id: "entity.group.singular" }),
        plural: msg("Groups", { id: "entity.group.plural" }),
    };

    protected override get searchPlaceholder() {
        return msg("Search for a group by name...", {
            id: "search.placeholder.",
        });
    }

    public pageDescription = msg(
        "Group users together and give them permissions based on the membership.",
        {
            id: "page.description.groups-list",
        },
    );
    public pageIcon = "pf-icon pf-icon-users";
    public supportsQL = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ...(await this.defaultEndpointConfig()),
            includeUsers: false,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Parent"), "parent"],
        [msg("Members")],
        [msg("Superuser privileges?")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

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

    row(item: Group): SlottedTemplateResult[] {
        return [
            html`<a
                href="#/identity/groups/${item.pk}"
                aria-label=${msg(str`View details of group "${item.name}"`)}
                >${item.name}</a
            >`,
            html`${item.parentName || msg("-")}`,
            html`${Array.from(item.users || []).length}`,
            html`<ak-status-label type="neutral" ?good=${item.isSuperuser}></ak-status-label>`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${this.updateEntityLabel}</span>
                    <span slot="header">${this.editEntityLabel}</span>
                    <ak-group-form slot="form" .instancePk=${item.pk}> </ak-group-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${this.editEntityLabel}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
            </div>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${this.createEntityLabel}</span>
                <span slot="header">${this.newEntityActionLabel}</span>
                <ak-group-form slot="form"> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${this.newEntityActionLabel}
                </button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-list": GroupListPage;
    }
}
