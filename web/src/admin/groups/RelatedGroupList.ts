import "#admin/users/ak-user-group-table";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/HorizontalFormElement";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";

import { modalInvoker, renderModal } from "#elements/dialogs";
import { AKFormSubmitEvent, Form } from "#elements/forms/Form";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { GroupForm } from "#admin/groups/ak-group-form";

import { CoreApi, Group, RbacApi, Role, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-group-related-add")
export class RelatedGroupAdd extends Form<{ groups: string[] }> {
    public static override verboseName = msg("Group");
    public static override submitVerb = msg("Add");
    public static override createLabel = msg("Add");

    @property({ attribute: false })
    public user?: User;

    @property({ attribute: false })
    public targetRole?: Role | null = null;

    @state()
    public groupsToAdd: Group[] = [];

    public override getSuccessMessage(): string {
        return msg("Successfully added group(s).");
    }

    protected async send(data: { groups: string[] }): Promise<unknown> {
        await Promise.all(
            data.groups.map((group) => {
                if (this.user) {
                    return aki(CoreApi).coreGroupsAddUserCreate({
                        groupUuid: group,
                        userAccountRequest: {
                            pk: this.user?.pk || 0,
                        },
                    });
                } else if (this.targetRole) {
                    return aki(RbacApi).rbacRolesAddGroupCreate({
                        uuid: this.targetRole!.pk,
                        groupSerializerForRoleRequest: {
                            pk: group,
                        }
                    });
                }
            }),
        );

        return data;
    }

    protected openUserGroupSelectModal = () => {
        return renderModal(html`
            <ak-form
                headline=${msg("Select Groups")}
                submit-label=${msg("Confirm")}
                @submit=${(event: AKFormSubmitEvent<Group[]>) => {
                    this.groupsToAdd = event.target.toJSON();
                }}
                ><ak-user-group-table></ak-user-group-table>
            </ak-form>
        `);
    };

    protected override renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Groups to add")} name="groups">
            <div class="pf-c-input-group">
                <button
                    class="pf-c-button pf-m-control"
                    type="button"
                    @click=${this.openUserGroupSelectModal}
                >
                    <pf-tooltip position="top" content=${msg("Add group")}>
                        <i class="fas fa-plus" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
                <div class="pf-c-form-control">
                    <ak-chip-group
                        @click=${this.openUserGroupSelectModal}
                        placeholder=${msg("Select one or more groups...")}
                    >
                        ${this.groupsToAdd.map((group) => {
                            return html`<ak-chip
                                removable
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
        </ak-form-element-horizontal>`;
    }
}

@customElement("ak-group-related-list")
export class RelatedGroupList extends Table<Group> {
    checkbox = true;
    clearOnRefresh = true;
    protected override searchEnabled = true;

    @property()
    order = "name";

    @property({ attribute: false })
    targetUser?: User;

    @property({ attribute: false})
    targetRole: Role | null = null;

    async apiEndpoint(): Promise<PaginatedResponse<Group>> {
        return aki(CoreApi).coreGroupsList({
            ...(await this.defaultEndpointConfig()),
            ...(this.targetUser && {membersByPk: [this.targetUser.pk]}),
            ...(this.targetRole && {rolesByPk: [this.targetRole.pk]}),
            includeUsers: false,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Superuser privileges?")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;

        if (this.targetRole) {
            return html`<ak-forms-delete-bulk
                object-label=${msg("Group(s)")}
                submit-label=${msg("Remove from Role")}
                action-subtext=${msg(
                    str`Are you sure you want to remove the following groups from role ${this.targetRole.name}?`,
                )}
                button-label=${msg("Remove")}
                .objects=${this.selectedElements}
                .delete=${(item: Group) => {
                    if (!this.targetRole) return;
                    return aki(RbacApi).rbacRolesRemoveGroupCreate({
                        uuid: this.targetRole.pk,
                        groupSerializerForRoleRequest: {
                            pk: item.pk,
                        },
                    });
                }}
            >
                <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                    ${msg("Remove")}
                </button>
            </ak-forms-delete-bulk>`;
        }

        return html`<ak-forms-delete-bulk
            object-label=${msg("Group(s)")}
            submit-label=${msg("Remove from Group(s)")}
            action-subtext=${msg(
                str`Are you sure you want to remove user ${this.targetUser?.username} from the following groups?`,
            )}
            button-label=${msg("Remove")}
            .objects=${this.selectedElements}
            .delete=${(item: Group) => {
                if (!this.targetUser) return;
                return aki(CoreApi).coreGroupsRemoveUserCreate({
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

    row(item: Group): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.pk}">${item.name}</a>`,
            html`<ak-status-label type="neutral" ?good=${item.isSuperuser}></ak-status-label>`,
            html`<button
                class="pf-c-button pf-m-plain"
                ${modalInvoker(GroupForm, { instancePk: item.pk })}
            >
                <pf-tooltip position="top" content=${msg("Edit")}>
                    <i class="fas fa-edit" aria-hidden="true"></i>
                </pf-tooltip>
            </button>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            ${this.targetUser
                ? html`<button
                      class="pf-c-button pf-m-primary"
                      ${modalInvoker(RelatedGroupAdd, { user: this.targetUser })}
                  >
                      ${msg("Add to existing group")}
                  </button>`
                : nothing}
            ${this.targetRole
                ? html`<button
                       class="pf-c-button pf-m-primary"
                       @click=${this.openAddGroupToTargetRoleModal}
                  >
                    ${msg("Add Existing Group")}
                  </button>`
                : html`<button class="pf-c-button pf-m-secondary" ${modalInvoker(GroupForm)}>
                        ${msg("Add new group")}
                      </button>`}
            ${super.renderToolbar()}
        `;
    }

    protected openAddGroupToTargetRoleModal = () => {
        return renderModal(
            html`<ak-group-related-add .targetRole=${this.targetRole}>
            </ak-group-related-add>`
        )
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-related-list": RelatedGroupList;
        "ak-group-related-add": RelatedGroupAdd;
    }
}
