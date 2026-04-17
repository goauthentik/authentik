import "#admin/groups/RelatedGroupList";
import "#admin/groups/RelatedUserList";
import "#admin/rbac/ak-rbac-object-permission-page";
import "#admin/lifecycle/ObjectLifecyclePage";
import "#admin/events/ObjectChangelog";
import "#admin/events/UserEvents";
import "#elements/Tabs";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { modalInvoker } from "#elements/dialogs";
import { WithLicenseSummary } from "#elements/mixins/license";

import { setPageDetails } from "#components/ak-page-navbar";
import { renderDescriptionList } from "#components/DescriptionList";

import { RoleForm } from "#admin/roles/ak-role-form";

import { ContentTypeEnum, ModelEnum, RbacApi, Role } from "@goauthentik/api";

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
export class RoleViewPage extends WithLicenseSummary(AKElement) {
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
                                    [
                                        msg("Related actions"),
                                        html`<button
                                            class="pf-c-button pf-m-primary pf-m-block"
                                            ${modalInvoker(RoleForm, {
                                                instancePk: this.targetRole.pk,
                                            })}
                                        >
                                            ${msg("Edit")}
                                        </button>`,
                                    ],
                                ])}
                            </div>
                        </div>
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${msg("Changelog")}</div>
                            <ak-object-changelog
                                targetModelPk=${this.targetRole.pk}
                                targetModelName=${ModelEnum.AuthentikRbacRole}
                            >
                            </ak-object-changelog>
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
                        <ak-user-related-list .targetRole=${this.targetRole}>
                        </ak-user-related-list>
                    </div>
                </section>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${ModelEnum.AuthentikRbacRole}
                    objectPk=${this.targetRole.pk}
                ></ak-rbac-object-permission-page>
                ${this.hasEnterpriseLicense
                    ? html`<ak-object-lifecycle-page
                          role="tabpanel"
                          tabindex="0"
                          slot="page-lifecycle"
                          id="page-lifecycle"
                          aria-label="${msg("Lifecycle")}"
                          model=${ContentTypeEnum.AuthentikRbacRole}
                          object-pk=${this.targetRole.pk}
                      ></ak-object-lifecycle-page>`
                    : nothing}
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
