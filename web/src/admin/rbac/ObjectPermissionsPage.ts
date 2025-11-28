import "#admin/rbac/RoleObjectPermissionTable";
import "#admin/rbac/UserObjectPermissionTable";
import "#admin/roles/RoleAssignedGlobalPermissionsTable";
import "#admin/roles/RoleAssignedObjectPermissionTable";
import "#admin/users/UserAssignedGlobalPermissionsTable";
import "#admin/users/UserAssignedObjectPermissionsTable";
import "#elements/Tabs";

import { AKElement } from "#elements/Base";

import { RbacPermissionsAssignedByUsersListModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-rbac-object-permission-page")
export class ObjectPermissionPage extends AKElement {
    @property()
    model?: RbacPermissionsAssignedByUsersListModelEnum;

    @property()
    objectPk?: string | number;

    @property({ type: Boolean })
    embedded = false;

    static styles = [PFBase, PFGrid, PFPage, PFCard];

    render() {
        return html` <ak-tabs pageIdentifier="permissionPage" ?vertical=${!this.embedded}>
            ${this.model === RbacPermissionsAssignedByUsersListModelEnum.AuthentikCoreUser
                ? this.renderCoreUser()
                : nothing}
            ${this.model === RbacPermissionsAssignedByUsersListModelEnum.AuthentikRbacRole
                ? this.renderRbacRole()
                : nothing}
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-object-user"
                id="page-object-user"
                aria-label="${msg("User Object Permissions")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("User Object Permissions")}</div>
                        <div class="pf-c-card__body">
                            ${msg("Permissions set on users which affect this object.")}
                        </div>
                        <div class="pf-c-card__body">
                            <ak-rbac-user-object-permission-table
                                .model=${this.model}
                                .objectPk=${this.objectPk}
                            >
                            </ak-rbac-user-object-permission-table>
                        </div>
                    </div>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-object-role"
                id="page-object-role"
                aria-label="${msg("Role Object Permissions")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Role Object Permissions")}</div>
                        <div class="pf-c-card__body">
                            ${msg("Permissions set on roles which affect this object.")}
                        </div>
                        <div class="pf-c-card__body">
                            <ak-rbac-role-object-permission-table
                                .model=${this.model}
                                .objectPk=${this.objectPk}
                            >
                            </ak-rbac-role-object-permission-table>
                        </div>
                    </div>
                </div>
            </div>
        </ak-tabs>`;
    }

    renderCoreUser() {
        return html`
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-assigned-global-permissions"
                id="page-assigned-global-permissions"
                aria-label="${msg("Assigned global permissions")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__title">${msg("Assigned global permissions")}</div>
                    <div class="pf-c-card__body">
                        ${msg(
                            "Permissions assigned to this user which affect all object instances of a given type.",
                        )}
                    </div>
                    <div class="pf-c-card__body">
                        <ak-user-assigned-global-permissions-table
                            userId=${this.objectPk as number}
                        >
                        </ak-user-assigned-global-permissions-table>
                    </div>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-assigned-object-permissions"
                id="page-assigned-object-permissions"
                aria-label="${msg("Assigned object permissions")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__title">${msg("Assigned object permissions")}</div>
                    <div class="pf-c-card__body">
                        ${msg(
                            "Permissions assigned to this user affecting specific object instances.",
                        )}
                    </div>
                    <div class="pf-c-card__body">
                        <ak-user-assigned-object-permissions-table
                            userId=${this.objectPk as number}
                        >
                        </ak-user-assigned-object-permissions-table>
                    </div>
                </div>
            </div>
        `;
    }

    renderRbacRole() {
        return html`
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-assigned-global-permissions"
                id="page-assigned-global-permissions"
                aria-label="${msg("Assigned global permissions")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__title">${msg("Assigned global permissions")}</div>
                    <div class="pf-c-card__body">
                        ${msg(
                            "Permissions assigned to this role which affect all object instances of a given type.",
                        )}
                    </div>
                    <div class="pf-c-card__body">
                        <ak-role-assigned-global-permissions-table
                            roleUuid=${this.objectPk as string}
                        >
                        </ak-role-assigned-global-permissions-table>
                    </div>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-assigned-object-permissions"
                id="page-assigned-object-permissions"
                aria-label="${msg("Assigned object permissions")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__title">${msg("Assigned object permissions")}</div>
                    <div class="pf-c-card__body">
                        ${msg(
                            "Permissions assigned to this user affecting specific object instances.",
                        )}
                    </div>
                    <div class="pf-c-card__body">
                        <ak-role-assigned-object-permissions-table
                            roleUuid=${this.objectPk as string}
                        >
                        </ak-role-assigned-object-permissions-table>
                    </div>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-object-permission-page": ObjectPermissionPage;
    }
}
