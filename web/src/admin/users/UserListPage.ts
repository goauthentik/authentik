import "#admin/reports/ExportButton";
import "#admin/users/ServiceAccountForm";
import "#admin/users/UserActiveForm";
import "#admin/users/UserBulkRevokeSessionsForm";
import "#admin/users/UserForm";
import "#admin/users/UserImpersonateForm";
import "#admin/users/UserPasswordForm";
import "#admin/users/UserResetEmailForm";
import "#admin/users/UserRecoveryLinkForm";
import "#components/ak-status-label";
import "#elements/TreeView";
import "#elements/buttons/ActionButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { userTypeToLabel } from "#common/labels";
import { DefaultUIConfig } from "#common/ui/config";
import { formatUserDisplayName } from "#common/users";

import { WithBrandConfig } from "#elements/mixins/branding";
import { CapabilitiesEnum, WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithSession } from "#elements/mixins/session";
import { modalInvoker } from "#elements/modals/utils";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { ServiceAccountForm } from "#admin/users/ServiceAccountForm";
import { UserForm } from "#admin/users/UserForm";
import { UserImpersonateForm } from "#admin/users/UserImpersonateForm";

import { CoreApi, CoreUsersExportCreateRequest, User, UserPath } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

export const renderRecoveryButtons = ({
    user,
    brandHasRecoveryFlow,
    buttonClasses,
}: {
    user: User;
    brandHasRecoveryFlow: boolean;
    buttonClasses?: string;
}) => {
    return html`<button
            class="pf-c-button pf-m-secondary ${buttonClasses || ""}"
            type="button"
            ${modalInvoker(() => {
                return html`<ak-user-password-form
                    headline=${msg(str`Update ${user.name || user.username}'s password`)}
                    username=${user.username}
                    email=${ifDefined(user.email)}
                    .instancePk=${user.pk}
                ></ak-user-password-form>`;
            })}
        >
            ${msg("Set password")}
        </button>
        ${brandHasRecoveryFlow
            ? html`
                  <ak-forms-modal id="ak-link-recovery-request">
                      <span slot="submit"> ${msg("Create link")} </span>
                      <span slot="header"> ${msg("Create recovery link")} </span>
                      <ak-user-recovery-link-form slot="form" .user=${user}>
                      </ak-user-recovery-link-form>
                      <button
                          slot="trigger"
                          class="pf-c-button pf-m-secondary ${buttonClasses || ""}"
                      >
                          ${msg("Create recovery link")}
                      </button>
                  </ak-forms-modal>
                  ${user.email
                      ? html`<ak-forms-modal id="ak-email-recovery-request">
                            <span slot="submit">${msg("Send link")}</span>
                            <span slot="header">${msg("Send recovery link to user")}</span>
                            <ak-user-reset-email-form slot="form" .user=${user}>
                            </ak-user-reset-email-form>
                            <button
                                slot="trigger"
                                class="pf-c-button pf-m-secondary ${buttonClasses || ""}"
                            >
                                ${msg("Email recovery link")}
                            </button>
                        </ak-forms-modal>`
                      : html`<p>
                            ${msg("To email a recovery link, set an email address for this user.")}
                        </p>`}
              `
            : html` <p>
                  ${msg("To create a recovery link, set a recovery flow for the current brand.")}
              </p>`}`;
};

const recoveryButtonStyles = css`
    #recovery-request-buttons {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        gap: 0.375rem;
    }
`;

@customElement("ak-user-list")
export class UserListPage extends WithBrandConfig(
    WithCapabilitiesConfig(WithSession(TablePage<User>)),
) {
    static styles: CSSResult[] = [
        ...TablePage.styles,
        PFDescriptionList,
        PFCard,
        PFAlert,
        recoveryButtonStyles,
    ];

    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override supportsQL = true;

    protected override searchEnabled = true;
    public override searchPlaceholder = msg("Search by username, email, etc...");
    public override searchLabel = msg("User Search");

    public pageTitle = msg("Users");
    public pageDescription = "";
    public pageIcon = "pf-icon pf-icon-user";

    @property()
    order = "last_login";

    @property()
    activePath;

    @state()
    hideDeactivated = getURLParam<boolean>("hideDeactivated", false);

    @state()
    userPaths?: UserPath;

    constructor() {
        super();
        const defaultPath = DefaultUIConfig.defaults.userPath;
        this.activePath = getURLParam<string>("path", defaultPath);
        if (this.uiConfig.defaults.userPath !== defaultPath) {
            this.activePath = this.uiConfig.defaults.userPath;
        }
    }

    protected canImpersonate = false;

    public override connectedCallback(): void {
        super.connectedCallback();

        this.canImpersonate = this.can(CapabilitiesEnum.CanImpersonate);
    }

    async apiEndpoint(): Promise<PaginatedResponse<User>> {
        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ...(await this.defaultEndpointConfig()),
            pathStartswith: this.activePath,
            isActive: this.hideDeactivated ? true : undefined,
            includeGroups: false,
        });
        this.userPaths = await new CoreApi(DEFAULT_CONFIG).coreUsersPathsRetrieve({
            search: this.search,
        });
        return users;
    }

    protected override rowLabel(item: User): string {
        if (item.name) {
            return msg(str`${item.username} (${item.name})`);
        }

        return item.username;
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Active"), "is_active"],
        [msg("Last login"), "last_login"],
        [msg("Type"), "type"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        const { currentUser, originalUser } = this;

        const shouldShowWarning = this.selectedElements.find((el) => {
            return el.pk === currentUser?.pk || el.pk === originalUser?.pk;
        });
        return html`<ak-user-bulk-revoke-sessions .users=${this.selectedElements}>
                <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-warning">
                    ${msg("Revoke Sessions")}
                </button>
            </ak-user-bulk-revoke-sessions>
            <ak-forms-delete-bulk
                object-label=${msg("User(s)")}
                .objects=${this.selectedElements}
                .metadata=${(item: User) => {
                    return [
                        { key: msg("Username"), value: item.username },
                        { key: msg("ID"), value: item.pk.toString() },
                        { key: msg("UID"), value: item.uid },
                    ];
                }}
                .usedBy=${(item: User) => {
                    return new CoreApi(DEFAULT_CONFIG).coreUsersUsedByList({
                        id: item.pk,
                    });
                }}
                .delete=${(item: User) => {
                    return new CoreApi(DEFAULT_CONFIG).coreUsersDestroy({
                        id: item.pk,
                    });
                }}
            >
                ${shouldShowWarning
                    ? html`<div slot="notice" class="pf-c-form__alert">
                          <div class="pf-c-alert pf-m-inline pf-m-warning">
                              <div class="pf-c-alert__icon">
                                  <i class="fas fa-exclamation-circle" aria-hidden="true"></i>
                              </div>
                              <h4 class="pf-c-alert__title">
                                  ${msg(
                                      str`Warning: You're about to delete the user you're logged in as (${shouldShowWarning.username}). Proceed at your own risk.`,
                                  )}
                              </h4>
                          </div>
                      </div>`
                    : nothing}
                <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                    ${msg("Delete")}
                </button>
            </ak-forms-delete-bulk>`;
    }

    protected override renderToolbarAfter(): TemplateResult {
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <div class="pf-c-input-group">
                    <label
                        class="pf-c-switch"
                        for="hide-deactivated-users"
                        aria-labelledby="hide-deactivated-users-label"
                    >
                        <input
                            id="hide-deactivated-users"
                            class="pf-c-switch__input"
                            type="checkbox"
                            ?checked=${!this.hideDeactivated}
                            @change=${() => {
                                this.hideDeactivated = !this.hideDeactivated;
                                this.page = 1;
                                this.fetch();
                                updateURLParams({
                                    hideDeactivated: this.hideDeactivated,
                                });
                            }}
                        />
                        <span class="pf-c-switch__toggle">
                            <span class="pf-c-switch__toggle-icon">
                                <i class="fas fa-check" aria-hidden="true"></i>
                            </span>
                        </span>
                        <span class="pf-c-switch__label" id="hide-deactivated-users-label">
                            ${msg("Show deactivated users")}
                        </span>
                    </label>
                </div>
            </div>
        </div>`;
    }

    protected row(item: User): SlottedTemplateResult[] {
        const { currentUser } = this;

        const showImpersonation = this.canImpersonate && currentUser && item.pk !== currentUser.pk;

        const displayName = formatUserDisplayName(item);

        return [
            html`<a href="#/identity/users/${item.pk}">
                <div>${item.username}</div>
                <small>${item.name ? item.name : html`&lt;${msg("No name set")}&gt;`}</small>
            </a>`,
            html`<ak-status-label ?good=${item.isActive}></ak-status-label>`,
            Timestamp(item.lastLogin),
            html`${userTypeToLabel(item.type)}`,
            html`<div>
                <button
                    class="pf-c-button pf-m-plain"
                    ${UserForm.asEditModalInvoker(item.pk)}
                    aria-label=${msg(str`Edit ${displayName}`)}
                >
                    <pf-tooltip position="top" content=${msg("Edit")}>
                        <i class="fas fa-edit" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
                ${showImpersonation
                    ? html`<button
                          class="pf-c-button pf-m-tertiary"
                          ${UserImpersonateForm.asEditModalInvoker(item.pk)}
                          aria-label=${msg(str`Impersonate ${displayName}`)}
                      >
                          <pf-tooltip
                              position="top"
                              content=${msg("Temporarily assume the identity of this user")}
                          >
                              <span>${msg("Impersonate")}</span>
                          </pf-tooltip>
                      </button>`
                    : null}
            </div>`,
        ];
    }

    renderExpanded(item: User): TemplateResult {
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("User status")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        ${item.isActive ? msg("Active") : msg("Inactive")}
                    </div>
                    <div class="pf-c-description-list__text">
                        ${item.isSuperuser ? msg("Superuser") : msg("Regular user")}
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Change status")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        <ak-user-active-form
                            object-label=${msg("User")}
                            .obj=${item}
                            .delete=${() => {
                                return new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                                    id: item.pk,
                                    patchedUserRequest: {
                                        isActive: !item.isActive,
                                    },
                                });
                            }}
                        >
                            <button slot="trigger" class="pf-c-button pf-m-warning">
                                ${item.isActive ? msg("Deactivate") : msg("Activate")}
                            </button>
                        </ak-user-active-form>
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Recovery")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text" id="recovery-request-buttons">
                        ${renderRecoveryButtons({
                            user: item,
                            brandHasRecoveryFlow: Boolean(this.brand.flowRecovery),
                        })}
                    </div>
                </dd>
            </div>
        </dl>`;
    }

    protected openNewUserModal = () => {
        const form = new UserForm();

        form.defaultPath = this.activePath;

        form.showModal();
    };

    renderObjectCreate(): TemplateResult {
        return html`
            <button class="pf-c-button pf-m-primary" @click=${this.openNewUserModal}>
                ${msg("New User")}
            </button>
            <button
                class="pf-c-button pf-m-secondary"
                ${ServiceAccountForm.asModalInvoker({
                    closedBy: "none",
                })}
            >
                ${msg("New Service Account")}
            </button>
            <ak-reports-export-button
                .createExport=${(params: CoreUsersExportCreateRequest) => {
                    return new CoreApi(DEFAULT_CONFIG).coreUsersExportCreate(params);
                }}
                .exportParams=${async () => {
                    return {
                        ...(await this.defaultEndpointConfig()),
                        pathStartswith: this.activePath,
                        isActive: this.hideDeactivated ? true : undefined,
                    };
                }}
            ></ak-reports-export-button>
        `;
    }

    protected renderSidebarBefore(): TemplateResult {
        return html`<aside aria-labelledby="sidebar-left-panel-header" class="pf-c-sidebar__panel">
            <div class="pf-c-card">
                <div
                    role="heading"
                    aria-level="2"
                    id="sidebar-left-panel-header"
                    class="pf-c-card__title"
                >
                    ${msg("User folders")}
                </div>
                <div class="pf-c-card__body">
                    <ak-treeview
                        label=${msg("User paths")}
                        .items=${this.userPaths?.paths || []}
                        activePath=${this.activePath}
                        @ak-refresh=${(ev: CustomEvent<{ path: string }>) => {
                            this.activePath = ev.detail.path;
                        }}
                    ></ak-treeview>
                </div>
            </div>
        </aside>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-list": UserListPage;
    }
}
