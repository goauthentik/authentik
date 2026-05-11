import "#admin/reports/ExportButton";
import "#admin/users/UserActiveForm";
import "#admin/users/ak-user-wizard";
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

import { IconEditButton, modalInvoker } from "#elements/dialogs";
import { WithBrandConfig } from "#elements/mixins/branding";
import { CapabilitiesEnum, WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithSession } from "#elements/mixins/session";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AKUserWizard } from "#admin/users/ak-user-wizard";
import { RecoveryButtons } from "#admin/users/recovery";
import { ToggleUserActivationButton } from "#admin/users/UserActiveForm";
import { UserForm } from "#admin/users/UserForm";
import { UserImpersonateForm } from "#admin/users/UserImpersonateForm";

import { CoreApi, CoreUsersExportCreateRequest, User, UserPath } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { customElement, property, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

const recoveryButtonStyles = css`
    #recovery-request-buttons {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        gap: 0.375rem;
    }
`;

@customElement("ak-user-list")
export class UserListPage extends WithLicenseSummary(
    WithBrandConfig(WithCapabilitiesConfig(WithSession(TablePage<User>))),
) {
    static styles: CSSResult[] = [
        ...TablePage.styles,
        PFDescriptionList,
        PFCard,
        PFAlert,
        PFAvatar,
        recoveryButtonStyles,
        css`
            .pf-c-avatar {
                max-height: var(--pf-c-avatar--Height);
                max-width: var(--pf-c-avatar--Width);
                vertical-align: middle;
            }
            .pf-c-card.tree .pf-c-card__body {
                padding-left: 0;
                padding-right: 0;
            }
        `,
    ];

    #api = new CoreApi(DEFAULT_CONFIG);

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

    @property({ type: String })
    public order = "-last_login";

    @property({ type: String })
    public activePath: string;

    @state()
    protected hideDeactivated = getURLParam<boolean>("hideDeactivated", false);

    @state()
    protected userPaths: UserPath | null = null;

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
        const users = await this.#api.coreUsersList({
            ...(await this.defaultEndpointConfig()),
            pathStartswith: this.activePath,
            isActive: this.hideDeactivated ? true : undefined,
            includeGroups: false,
        });

        this.userPaths = await this.#api.coreUsersPathsRetrieve({
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
        ["", null, msg("Avatar")],
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
                    return this.#api.coreUsersUsedByList({
                        id: item.pk,
                    });
                }}
                .delete=${(item: User) => {
                    return this.#api.coreUsersDestroy({
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
                                      str`Warning: You are about to delete user ${shouldShowWarning.username}, but you are currently logged in as this user. Proceed at your own risk.`,
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

    protected row(item: User) {
        const { currentUser } = this;

        const showImpersonation = this.canImpersonate && currentUser && item.pk !== currentUser.pk;

        const displayName = formatUserDisplayName(item);

        return [
            html`<img
                class="pf-c-avatar pf-m-hidden pf-m-visible-on-xl"
                src=${item.avatar}
                alt=${msg(str`Avatar for ${displayName}`)}
            />`,
            html`<a
                href="#/identity/users/${item.pk}"
                aria-label=${msg(str`View details for ${displayName}`)}
            >
                <div aria-label=${msg(str`Username: ${item.username}`)}>${item.username}</div>
                <small aria-label=${msg(str`Display name: ${displayName || msg("No name set")}`)}
                    >${displayName ? item.name : html`&lt;${msg("No name set")}&gt;`}</small
                >
            </a>`,
            html`<ak-status-label ?good=${item.isActive}></ak-status-label>`,
            Timestamp(item.lastLogin),
            html`${userTypeToLabel(item.type)}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(UserForm, item.pk, displayName)}
                ${showImpersonation
                    ? html`<button
                          class="pf-c-button pf-m-tertiary"
                          ${UserImpersonateForm.asInstanceInvoker(item.pk)}
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
                        ${ToggleUserActivationButton(item)}
                    </div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${msg("Recovery")}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text" id="recovery-request-buttons">
                        ${RecoveryButtons({
                            user: item,
                            brandHasRecoveryFlow: Boolean(this.brand.flowRecovery),
                        })}
                    </div>
                </dd>
            </div>
        </dl>`;
    }

    protected buildExportParams = async () => {
        return {
            ...(await this.defaultEndpointConfig()),
            pathStartswith: this.activePath,
            isActive: this.hideDeactivated ? true : undefined,
        };
    };

    protected createExport = (params: CoreUsersExportCreateRequest) => {
        return this.#api.coreUsersExportCreate(params);
    };

    protected renderObjectCreate(): SlottedTemplateResult {
        const { activePath } = this;

        return guard([activePath], () => {
            return [
                html`<button
                    class="pf-c-button pf-m-primary"
                    type="button"
                    ${modalInvoker(AKUserWizard, {
                        defaultPath: activePath,
                    })}
                    aria-description=${msg("Open the new user wizard")}
                >
                    ${msg("New User")}
                </button> `,
                html`<ak-reports-export-button
                    .createExport=${this.createExport}
                    .exportParams=${this.buildExportParams}
                ></ak-reports-export-button> `,
            ];
        });
    }

    protected renderSidebarBefore(): TemplateResult {
        return html`<aside aria-labelledby="sidebar-left-panel-header" class="pf-c-sidebar__panel">
            <div class="pf-c-card tree">
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
