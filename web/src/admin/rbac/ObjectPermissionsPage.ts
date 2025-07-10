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
            <section
                slot="page-object-user"
                data-tab-title="${msg("User Object Permissions")}"
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
            </section>
            <section
                slot="page-object-role"
                data-tab-title="${msg("Role Object Permissions")}"
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
            </section>
        </ak-tabs>`;
    }

    renderCoreUser() {
        return html`
            <div
                slot="page-assigned-global-permissions"
                data-tab-title="${msg("Assigned global permissions")}"
            >
                <section class="pf-c-page__main-section pf-m-no-padding-mobile">
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
                </section>
            </div>
            <div
                slot="page-assigned-object-permissions"
                data-tab-title="${msg("Assigned object permissions")}"
            >
                <section class="pf-c-page__main-section pf-m-no-padding-mobile">
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
                </section>
            </div>
        `;
    }

    renderRbacRole() {
        return html`
            <div
                slot="page-assigned-global-permissions"
                data-tab-title="${msg("Assigned global permissions")}"
            >
                <section class="pf-c-page__main-section pf-m-no-padding-mobile">
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
                </section>
            </div>
            <div
                slot="page-assigned-object-permissions"
                data-tab-title="${msg("Assigned object permissions")}"
            >
                <section class="pf-c-page__main-section pf-m-no-padding-mobile">
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
                </section>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-object-permission-page": ObjectPermissionPage;
    }
}
