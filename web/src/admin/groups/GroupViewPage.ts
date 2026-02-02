import "#admin/groups/GroupForm";
import "#admin/groups/RelatedUserList";
import "#admin/rbac/ObjectPermissionsPage";
import "#admin/roles/RelatedRoleList";
import "#components/ak-object-attributes-card";
import "#components/ak-status-label";
import "#components/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/ModalForm";
import "#elements/ak-mdx/ak-mdx";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";

import { CoreApi, Group, RbacPermissionsAssignedByRolesListModelEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

@customElement("ak-group-view")
export class GroupViewPage extends AKElement {
    @property({ type: String })
    set groupId(id: string) {
        new CoreApi(DEFAULT_CONFIG)
            .coreGroupsRetrieve({
                groupUuid: id,
                includeUsers: false,
                includeInheritedRoles: true,
            })
            .then((group) => {
                this.group = group;
            });
    }

    @property({ attribute: false })
    group?: Group;

    static styles: CSSResult[] = [
        PFPage,
        PFButton,
        PFDisplay,
        PFGrid,
        PFList,
        PFContent,
        PFCard,
        PFDescriptionList,
        PFSizing,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.group?.pk) return;
            this.groupId = this.group?.pk;
        });
    }

    render(): SlottedTemplateResult {
        if (!this.group) {
            return nothing;
        }
        return html`<main>
            <ak-tabs>
                <section
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
                            <div class="pf-c-card__title">${msg("Group Info")}</div>
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
                                                ${this.group.name}
                                            </div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${msg("Superuser")}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <ak-status-label
                                                    type="neutral"
                                                    ?good=${this.group.isSuperuser}
                                                ></ak-status-label>
                                            </div>
                                        </dd>
                                    </div>
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${msg("Roles")}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <ul class="pf-c-list">
                                                    ${this.group.rolesObj.map((role) => {
                                                        return html`<li>
                                                            <a href=${`#/identity/roles/${role.pk}`}
                                                                >${role.name}
                                                            </a>
                                                        </li>`;
                                                    })}
                                                    ${(this.group.inheritedRolesObj ?? []).map(
                                                        (role) => {
                                                            return html`<li>
                                                                <a
                                                                    href=${`#/identity/roles/${role.pk}`}
                                                                    >${role.name}
                                                                </a>
                                                                <pf-tooltip
                                                                    position="top"
                                                                    content=${msg(
                                                                        "Inherited from parent group",
                                                                    )}
                                                                >
                                                                    <span
                                                                        class="pf-c-label pf-m-outline pf-m-cyan"
                                                                        style="margin-left: 0.5rem;"
                                                                    >
                                                                        <span
                                                                            class="pf-c-label__content"
                                                                            >${msg(
                                                                                "Inherited",
                                                                            )}</span
                                                                        >
                                                                    </span>
                                                                </pf-tooltip>
                                                            </li>`;
                                                        },
                                                    )}
                                                </ul>
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                            <div class="pf-c-card__footer">
                                <ak-forms-modal>
                                    <span slot="submit">${msg("Update")}</span>
                                    <span slot="header">${msg("Update Group")}</span>
                                    <ak-group-form slot="form" .instancePk=${this.group.pk}>
                                    </ak-group-form>
                                    <button slot="trigger" class="pf-m-primary pf-c-button">
                                        ${msg("Edit")}
                                    </button>
                                </ak-forms-modal>
                            </div>
                        </div>
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-9-col-on-xl pf-m-9-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${msg("Notes")}</div>
                            <div class="pf-c-card__body">
                                ${this.group?.attributes?.notes
                                    ? html`<ak-mdx
                                          .content=${this.group.attributes.notes}
                                      ></ak-mdx>`
                                    : html`
                                          <p>
                                              ${msg(
                                                  "Edit the notes attribute of this group to add notes here.",
                                              )}
                                          </p>
                                      `}
                            </div>
                        </div>
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-12-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${msg("Changelog")}</div>
                            <div class="pf-c-card__body">
                                <ak-object-changelog
                                    targetModelPk=${this.group.pk}
                                    targetModelApp="authentik_core"
                                    targetModelName="group"
                                >
                                </ak-object-changelog>
                            </div>
                        </div>
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <ak-object-attributes-card
                                .objectAttributes=${this.group.attributes}
                            ></ak-object-attributes-card>
                        </div>
                    </div>
                </section>
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
                            <ak-user-related-list .targetGroup=${this.group}>
                            </ak-user-related-list>
                        </div>
                    </div>
                </section>
                <section
                    role="tabpanel"
                    tabindex="0"
                    slot="page-roles"
                    id="page-roles"
                    aria-label="${msg("Roles")}"
                >
                    ${this.renderTabRoles(this.group)}
                </section>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikCoreGroup}
                    objectPk=${this.group.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }

    protected renderTabRoles(group: Group): TemplateResult {
        return html`
            <ak-tabs pageIdentifier="groupRoles" vertical>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-assigned-roles"
                    id="page-assigned-roles"
                    aria-label=${msg("Assigned Roles")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-role-related-list .targetGroup=${group}> </ak-role-related-list>
                        </div>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-all-roles"
                    id="page-all-roles"
                    aria-label=${msg("All Roles")}
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-role-related-list .targetGroup=${group} showInherited>
                            </ak-role-related-list>
                        </div>
                    </div>
                </div>
            </ak-tabs>
        `;
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-users",
            header: this.group?.name ? msg(str`Group ${this.group.name}`) : msg("Group"),
            description: this.group?.name,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-group-view": GroupViewPage;
    }
}
