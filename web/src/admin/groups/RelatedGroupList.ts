import "#admin/groups/GroupForm";
import "#admin/users/GroupSelectModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EntityLabel } from "#common/i18n/nouns";

import { Form } from "#elements/forms/Form";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, Group, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-group-related-add")
export class RelatedGroupAdd extends Form<{ groups: string[] }> {
    @property({ attribute: false })
    user?: User;

    @state()
    groupsToAdd: Group[] = [];

    protected override readonly actionName = "add";

    protected override entityLabel = msg("User To Group", { id: "entity.user-to-group.singular" });

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
        return html`<ak-form-element-horizontal label=${msg("Groups to add")} name="groups">
            <div class="pf-c-input-group">
                <ak-user-group-select-table
                    .confirm=${(items: Group[]) => {
                        this.groupsToAdd = items;
                        this.requestUpdate();
                        return Promise.resolve();
                    }}
                >
                    <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                        <pf-tooltip position="top" content=${msg("Add group")}>
                            <i class="fas fa-plus" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-user-group-select-table>
                <div class="pf-c-form-control">
                    <ak-chip-group>
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

    protected override entityLabel: EntityLabel = {
        singular: msg("Group", { id: "entity.group.singular" }),
        plural: msg("Groups", { id: "entity.group.plural" }),
    };

    @property()
    order = "name";

    @property({ attribute: false })
    targetUser?: User;

    async apiEndpoint(): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ...(await this.defaultEndpointConfig()),
            membersByPk: this.targetUser ? [this.targetUser.pk] : [],
            includeUsers: false,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name", { id: "column.name" }), "name"],
        [msg("Parent", { id: "column.parent" }), "parent"],
        [msg("Superuser privileges?", { id: "column.superuser-privileges-question-mark" })],
        [
            msg("Actions", { id: "column.actions" }),
            null,
            msg("Row Actions", { id: "column.row-actions" }),
        ],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Group(s)")}
            actionLabel=${msg("Remove from Group(s)")}
            actionSubtext=${msg(
                str`Are you sure you want to remove user ${this.targetUser?.username} from the following groups?`,
            )}
            buttonLabel=${msg("Remove")}
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

    row(item: Group): SlottedTemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.pk}">${item.name}</a>`,
            html`${item.parentName || msg("-")}`,
            html`<ak-status-label type="neutral" ?good=${item.isSuperuser}></ak-status-label>`,
            html` <ak-forms-modal>
                <span slot="submit">${this.updateEntityLabel}</span>
                <span slot="header">${this.editEntityLabel}</span>
                <ak-group-form slot="form" .instancePk=${item.pk}> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
            ${this.targetUser
                ? html`<ak-forms-modal>
                      <span slot="submit">${msg("Add")}</span>
                      <span slot="header">${msg("Add Group")}</span>
                      <ak-group-related-add .user=${this.targetUser} slot="form">
                      </ak-group-related-add>
                      <button slot="trigger" class="pf-c-button pf-m-primary">
                          ${msg("Add to existing group")}
                      </button>
                  </ak-forms-modal>`
                : nothing}
            <ak-forms-modal>
                <span slot="submit">${this.createEntityLabel}</span>
                <span slot="header">${this.newEntityActionLabel}</span>
                <ak-group-form slot="form"> </ak-group-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${msg("Add new group")}
                </button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-related-list": RelatedGroupList;
        "ak-group-related-add": RelatedGroupAdd;
    }
}
