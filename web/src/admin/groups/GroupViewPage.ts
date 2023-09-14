import "@goauthentik/admin/groups/GroupForm";
import "@goauthentik/admin/users/RelatedUserList";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ModalForm";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

import { CoreApi, Group } from "@goauthentik/api";

@customElement("ak-group-view")
export class GroupViewPage extends AKElement {
    @property({ type: String })
    set groupId(id: string) {
        new CoreApi(DEFAULT_CONFIG)
            .coreGroupsRetrieve({
                groupUuid: id,
            })
            .then((group) => {
                this.group = group;
            });
    }

    @property({ attribute: false })
    group?: Group;

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
            PFSizing,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.group?.pk) return;
            this.groupId = this.group?.pk;
        });
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon="pf-icon pf-icon-users"
                header=${msg(str`Group ${this.group?.name || ""}`)}
                description=${this.group?.name || ""}
            >
            </ak-page-header>
            ${this.renderBody()}`;
    }

    renderBody(): TemplateResult {
        if (!this.group) {
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
                        <div class="pf-c-card__title">${msg("Group Info")}</div>
                        <div class="pf-c-card__body">
                            <dl class="pf-c-description-list pf-m-2-col">
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
                                            <ak-label
                                                color=${this.group.isSuperuser
                                                    ? PFColor.Green
                                                    : PFColor.Orange}
                                            ></ak-label>
                                        </div>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                        <div class="pf-c-card__footer">
                            <ak-forms-modal>
                                <span slot="submit"> ${msg("Update")} </span>
                                <span slot="header"> ${msg("Update Group")} </span>
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
                            ${Object.hasOwn(this.group?.attributes || {}, "notes")
                                ? html`${this.group.attributes?.notes}`
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
                </div>
            </section>
            <section
                slot="page-users"
                data-tab-title="${msg("Users")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-user-related-list .targetGroup=${this.group}> </ak-user-related-list>
                    </div>
                </div>
            </section>
        </ak-tabs>`;
    }
}
