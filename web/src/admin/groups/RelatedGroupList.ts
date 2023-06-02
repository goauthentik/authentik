import "@goauthentik/admin/groups/GroupForm";
import "@goauthentik/admin/groups/GroupForm";
import "@goauthentik/admin/users/GroupSelectModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CoreApi, Group, User } from "@goauthentik/api";

@customElement("ak-group-related-add")
export class RelatedGroupAdd extends Form<{ groups: string[] }> {
    @property({ attribute: false })
    user?: User;

    @state()
    groupsToAdd: Group[] = [];

    getSuccessMessage(): string {
        return msg("Successfully added user to group(s).");
    }

    async send(data: { groups: string[] }): Promise<unknown> {
        await Promise.all(
            data.groups.map((group) => {
                return new CoreApi(DEFAULT_CONFIG).coreGroupsAddUserCreate({
                    groupUuid: group,
                    userAccountRequest: {
                        pk: this.user?.pk || 0,
                    },
                });
            }),
        );
        return data;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Groups to add")} name="groups">
                <div class="pf-c-input-group">
                    <ak-user-group-select-table
                        .confirm=${(items: Group[]) => {
                            this.groupsToAdd = items;
                            this.requestUpdate();
                            return Promise.resolve();
                        }}
                    >
                        <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                            <i class="fas fa-plus" aria-hidden="true"></i>
                        </button>
                    </ak-user-group-select-table>
                    <div class="pf-c-form-control">
                        <ak-chip-group>
                            ${this.groupsToAdd.map((group) => {
                                return html`<ak-chip
                                    .removable=${true}
                                    value=${ifDefined(group.pk)}
                                    @remove=${() => {
                                        const idx = this.groupsToAdd.indexOf(group);
                                        this.groupsToAdd.splice(idx, 1);
                                        this.requestUpdate();
                                    }}
                                >
                                    ${group.name}
                                </ak-chip>`;
                            })}
                        </ak-chip-group>
                    </div>
                </div>
            </ak-form-element-horizontal>
        </form> `;
    }
}

@customElement("ak-group-related-list")
export class RelatedGroupList extends Table<Group> {
    checkbox = true;
    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "name";

    @property({ attribute: false })
    targetUser?: User;

    async apiEndpoint(page: number): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            membersByPk: this.targetUser ? [this.targetUser.pk] : [],
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Parent"), "parent"),
            new TableColumn(msg("Superuser privileges?")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Group(s)")}
            actionLabel=${msg("Remove from Group(s)")}
            actionSubtext=${msg(
                str`Are you sure you want to remove user ${this.targetUser?.username} from the following groups?`,
            )}
            .objects=${this.selectedElements}
            .delete=${(item: Group) => {
                if (!this.targetUser) return;
                return new CoreApi(DEFAULT_CONFIG).coreGroupsRemoveUserCreate({
                    groupUuid: item.pk,
                    userAccountRequest: {
                        pk: this.targetUser?.pk || 0,
                    },
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Remove")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Group): TemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.pk}">${item.name}</a>`,
            html`${item.parentName || msg("-")}`,
            html`<ak-label color=${item.isSuperuser ? PFColor.Green : PFColor.Grey}>
                ${item.isSuperuser ? msg("Yes") : msg("No")}
            </ak-label>`,
            html` <ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update Group")} </span>
                <ak-group-form slot="form" .instancePk=${item.pk}> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            ${this.targetUser
                ? html`<ak-forms-modal>
                      <span slot="submit"> ${msg("Add")} </span>
                      <span slot="header"> ${msg("Add Group")} </span>
                      <ak-group-related-add .user=${this.targetUser} slot="form">
                      </ak-group-related-add>
                      <button slot="trigger" class="pf-c-button pf-m-primary">
                          ${msg("Add to existing group")}
                      </button>
                  </ak-forms-modal>`
                : html``}
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Group")} </span>
                <ak-group-form slot="form"> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${msg("Add new group")}
                </button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}
