import "#admin/groups/RelatedUserList";
import "#admin/rbac/ak-rbac-object-permission-page";
import "#admin/roles/ak-related-role-table";
import "#components/ak-object-attributes-card";
import "#admin/lifecycle/ObjectLifecyclePage";
import "#components/ak-status-label";
import "#admin/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/ak-mdx/ak-mdx";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { modalInvoker } from "#elements/dialogs";
import { WithLicenseSummary } from "#elements/mixins/license";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";
import renderDescriptionList from "#components/DescriptionList";

import { GroupForm } from "#admin/groups/ak-group-form";

import { ContentTypeEnum, CoreApi, Group, ModelEnum } from "@goauthentik/api";

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
export class GroupViewPage extends WithLicenseSummary(AKElement) {
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
                                ${renderDescriptionList([
                                    [msg("Name"), html`${this.group.name}`],
                                    [
                                        msg("Superuser"),
                                        html`<ak-status-label
                                            type="neutral"
                                            ?good=${this.group.isSuperuser}
                                        ></ak-status-label>`,
                                    ],
                                    [
                                        msg("Roles"),
                                        html`${this.group.rolesObj.length +
                                            (this.group.inheritedRolesObj ?? []).length <
                                        1
                                            ? html`-`
                                            : html`<ul class="pf-c-list">
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
                                                                          >${msg("Inherited")}</span
                                                                      >
                                                                  </span>
                                                              </pf-tooltip>
                                                          </li>`;
                                                      },
                                                  )}
                                              </ul>`} `,
                                    ],
                                    [
                                        msg("Related actions"),
                                        html`<button
                                            class="pf-c-button pf-m-primary pf-m-block"
                                            ${modalInvoker(GroupForm, {
                                                instancePk: this.group.pk,
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
                            <ak-object-changelog
                                targetModelPk=${this.group.pk}
                                targetModelName=${ModelEnum.AuthentikCoreGroup}
                            >
                            </ak-object-changelog>
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
                        <ak-user-related-list .targetGroup=${this.group}> </ak-user-related-list>
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
                    model=${ModelEnum.AuthentikCoreGroup}
                    objectPk=${this.group.pk}
                ></ak-rbac-object-permission-page>
                ${this.hasEnterpriseLicense
                    ? html`<ak-object-lifecycle-page
                          role="tabpanel"
                          tabindex="0"
                          slot="page-lifecycle"
                          id="page-lifecycle"
                          aria-label="${msg("Lifecycle")}"
                          model=${ContentTypeEnum.AuthentikCoreGroup}
                          object-pk=${this.group.pk}
                      ></ak-object-lifecycle-page>`
                    : nothing}
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
                        <ak-related-role-table .targetGroup=${group}> </ak-related-role-table>
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
                        <ak-related-role-table
                            .targetGroup=${group}
                            showInherited
                        ></ak-related-role-table>
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
