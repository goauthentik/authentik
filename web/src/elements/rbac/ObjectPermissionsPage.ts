import { AKElement } from "@goauthentik/app/elements/Base";
import "@goauthentik/app/elements/rbac/RoleObjectPermissionTable";
import "@goauthentik/app/elements/rbac/UserObjectPermissionTable";
import "@goauthentik/elements/Tabs";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { RbacPermissionsAssignedByUsersListModelEnum } from "@goauthentik/api";

@customElement("ak-rbac-object-permission-page")
export class ObjectPermissionPage extends AKElement {
    @property()
    model?: RbacPermissionsAssignedByUsersListModelEnum;

    @property()
    objectPk?: string | number;

    static get styles(): CSSResult[] {
        return [PFBase, PFGrid, PFPage, PFCard];
    }
    render(): TemplateResult {
        return html`<ak-tabs pageIdentifier="permissionPage">
            <section
                slot="page-object-user"
                data-tab-title="${msg("User Object Permissions")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">User Object Permissions</div>
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
                        <div class="pf-c-card__title">Role Object Permissions</div>
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
}
