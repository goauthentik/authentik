import "@goauthentik/admin/groups/RelatedGroupList";
import "@goauthentik/app/admin/roles/RolePermissionGlobalTable";
import "@goauthentik/app/admin/roles/RolePermissionObjectTable";
import "@goauthentik/app/elements/rbac/ObjectPermissionsPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import "@goauthentik/components/events/UserEvents";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

import { RbacApi, RbacPermissionsAssignedByUsersListModelEnum, Role } from "@goauthentik/api";

@customElement("ak-role-view")
export class RoleViewPage extends AKElement {
    @property({ type: String })
    set roleId(id: string) {
        new RbacApi(DEFAULT_CONFIG)
            .rbacRolesRetrieve({
                uuid: id,
            })
            .then((role) => {
                this._role = role;
            });
    }

    @state()
    _role?: Role;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFButton,
            PFDisplay,
            PFGrid,
            PFContent,
            PFCard,
            PFDescriptionList,
            css`
                .pf-c-description-list__description ak-action-button {
                    margin-right: 6px;
                    margin-bottom: 6px;
                }
                .ak-button-collection {
                    max-width: 12em;
                }
            `,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this._role?.pk) return;
            this.roleId = this._role?.pk;
        });
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon="fa fa-lock"
                header=${msg(str`Role ${this._role?.name || ""}`)}
            >
            </ak-page-header>
            ${this.renderBody()}`;
    }

    renderBody(): TemplateResult {
        if (!this._role) {
            return html``;
        }
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-3-col-on-xl pf-m-3-col-on-2xl"
                    >
                        <div class="pf-c-card__title">${msg("Role Info")}</div>
                        <div class="pf-c-card__body">
                            <dl class="pf-c-description-list">
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${msg("Name")}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this._role.name}
                                        </div>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                    </div>
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                    >
                        <div class="pf-c-card__title">${msg("Assigned global permissions")}</div>
                        <div class="pf-c-card__body">
                            <ak-role-permissions-global-table
                                roleUuid=${this._role.pk}
                            ></ak-role-permissions-global-table>
                        </div>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Assigned object permissions")}</div>
                        <div class="pf-c-card__body">
                            <ak-role-permissions-object-table
                                roleUuid=${this._role.pk}
                            ></ak-role-permissions-object-table>
                        </div>
                    </div>
                </div>
            </section>
            <ak-rbac-object-permission-page
                slot="page-permissions"
                data-tab-title="${msg("Permissions")}"
                model=${RbacPermissionsAssignedByUsersListModelEnum.RbacRole}
                objectPk=${this._role.pk}
            ></ak-rbac-object-permission-page>
        </ak-tabs>`;
    }
}
