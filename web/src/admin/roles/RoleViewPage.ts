import "#admin/groups/RelatedGroupList";
import "#admin/groups/RelatedUserList";
import "#admin/rbac/ObjectPermissionsPage";
import "#admin/roles/RoleForm";
import "#components/events/ObjectChangelog";
import "#components/events/UserEvents";
import "#elements/Tabs";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";
import { renderDescriptionList } from "#components/DescriptionList";

import { RbacApi, RbacPermissionsAssignedByRolesListModelEnum, Role } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

@customElement("ak-role-view")
export class RoleViewPage extends AKElement {
    @property({ type: String })
    set roleId(id: string) {
        new RbacApi(DEFAULT_CONFIG)
            .rbacRolesRetrieve({
                uuid: id,
            })
            .then((role) => {
                this.targetRole = role;
            });
    }

    @state()
    targetRole?: Role;

    static styles = [
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
                max-width: 13em;
            }
        `,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.targetRole?.pk) return;
            this.roleId = this.targetRole?.pk;
        });
    }

    renderUpdateControl(role: Role) {
        return html` <div class="pf-c-description-list__text">
            <ak-forms-modal>
                <span slot="submit">${msg("Update")}</span>
                <span slot="header">${msg("Update Role")}</span>
                <ak-role-form slot="form" .instancePk=${role.pk}> </ak-role-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Edit")}</button>
            </ak-forms-modal>
        </div>`;
    }

    render() {
        if (!this.targetRole) {
            return nothing;
        }

        return html`<main part="main">
            <ak-tabs part="tabs">
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-3-col-on-xl pf-m-3-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${msg("Role Info")}</div>
                            <div class="pf-c-card__body">
                                ${renderDescriptionList([
                                    [msg("Name"), this.targetRole.name],
                                    [msg("Edit"), this.renderUpdateControl(this.targetRole)],
                                ])}
                            </div>
                        </div>
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${msg("Changelog")}</div>
                            <div class="pf-c-card__body">
                                <ak-object-changelog
                                    targetModelPk=${this.targetRole.pk}
                                    targetModelApp="authentik_rbac"
                                    targetModelName="role"
                                >
                                </ak-object-changelog>
                            </div>
                        </div>
                    </div>
                </div>
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-users"
                    id="page-users"
                    aria-label="${msg("Users")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-related-list .targetRole=${this.targetRole}>
                            </ak-user-related-list>
                        </div>
                    </div>
                </section>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikRbacRole}
                    objectPk=${this.targetRole.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "fa fa-lock",
            header: this.targetRole?.name ? msg(str`Role ${this.targetRole.name}`) : msg("Role"),
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-role-view": RoleViewPage;
    }
}
