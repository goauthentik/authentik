import "@goauthentik/admin/groups/RelatedGroupList";
import "@goauthentik/admin/roles/RoleForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { renderDescriptionList } from "@goauthentik/components/DescriptionList";
import "@goauthentik/components/events/ObjectChangelog";
import "@goauthentik/components/events/UserEvents";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/rbac/ObjectPermissionsPage";

import { msg, str } from "@lit/localize";
import { css, html, nothing } from "lit";
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

    static get styles() {
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

    render() {
        return html`<ak-page-header
                icon="fa fa-lock"
                header=${msg(str`Role ${this._role?.name || ""}`)}
            >
            </ak-page-header>
            ${this.renderBody()}`;
    }

    renderUpdateControl(role: Role) {
        return html` <div class="pf-c-description-list__text">
            <ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg("Update Role")} </span>
                <ak-role-form slot="form" .instancePk=${role.pk}> </ak-role-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Edit")}</button>
            </ak-forms-modal>
        </div>`;
    }

    renderBody() {
        if (!this._role) {
            return nothing;
        }

        return html` <ak-tabs>
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
                            ${renderDescriptionList([
                                [msg("Name"), this._role.name],
                                [msg("Edit"), this.renderUpdateControl(this._role)],
                            ])}
                        </div>
                    </div>
                    <div
                        class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                    >
                        <div class="pf-c-card__title">${msg("Changelog")}</div>
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.roleId}
                                targetModelApp="authentik_rbac"
                                targetModelName="role"
                            >
                            </ak-object-changelog>
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
