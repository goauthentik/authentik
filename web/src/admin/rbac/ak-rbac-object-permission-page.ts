import "#admin/rbac/ak-rbac-role-object-permission-table";
import "#admin/roles/ak-role-assigned-global-permissions-table";
import "#admin/roles/ak-role-assigned-object-permissions-table";
import "#elements/Tabs";

import { AKElement } from "#elements/Base";
import { ifPresent } from "#elements/utils/attributes";

import { ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-rbac-object-permission-page")
export class ObjectPermissionPage extends AKElement {
    static styles = [
        PFGrid,
        PFPage,
        PFCard,
        css`
            :host {
                display: block;
            }
        `,
    ];

    @property()
    public model?: ModelEnum;

    // TODO: Use attribute casing.
    // @property({ attribute: "object-pk" })
    @property()
    public objectPk: string | null = null;

    @property({ type: Boolean })
    public embedded = false;

    render() {
        return this.model === ModelEnum.AuthentikRbacRole
            ? html`<ak-tabs pageIdentifier="permissionPage" ?vertical=${!this.embedded}>
                  ${this.renderPermissionsAssignedToRole()}
              </ak-tabs>`
            : html`<div class="pf-c-page__main-section pf-m-no-padding-mobile">
                  ${this.renderPermissionsOnObject()}
              </div>`;
    }

    renderPermissionsOnObject() {
        return html`<ak-rbac-role-object-permission-table
            .model=${this.model}
            .objectPk=${this.objectPk}
        >
        </ak-rbac-role-object-permission-table>`;
    }

    protected renderPermissionsAssignedToRole() {
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
                    <ak-role-assigned-global-permissions-table
                        role-uuid=${ifPresent(this.objectPk)}
                    >
                    </ak-role-assigned-global-permissions-table>
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
                            "Permissions assigned to this role affecting specific object instances.",
                        )}
                    </div>
                    <ak-role-assigned-object-permissions-table
                        role-uuid=${ifPresent(this.objectPk)}
                    >
                    </ak-role-assigned-object-permissions-table>
                </div>
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-object-role"
                id="page-object-role"
                aria-label="${msg("Permissions on this object")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Permissions on this object")}</div>
                        <div class="pf-c-card__body">
                            ${msg("Permissions set on roles which affect this object.")}
                        </div>
                        ${this.renderPermissionsOnObject()}
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
