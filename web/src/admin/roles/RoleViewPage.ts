import "@goauthentik/admin/groups/RelatedGroupList";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import "@goauthentik/components/events/ObjectChangelog";
import "@goauthentik/components/events/UserEvents";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";

import { CoreApi, Role } from "@goauthentik/api";

@customElement("ak-role-view")
export class UserViewPage extends AKElement {
    @property({ type: String })
    set roleId(id: string) {
        new CoreApi(DEFAULT_CONFIG)
            .coreRolesRetrieve({
                uuid: id,
            })
            .then((role) => {
                this._role = role;
            });
    }

    @state()
    _role?: Role;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFFlex,
            PFButton,
            PFDisplay,
            PFGrid,
            PFContent,
            PFCard,
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

    render(): TemplateResult {
        return html`<ak-page-header
                icon="pf-icon pf-icon-users"
                header=${msg(str`Role ${this._role?.name || ""}`)}
            >
            </ak-page-header>
            ${this.renderBody()}`;
    }

    renderBody(): TemplateResult {
        if (!this._role) {
            return html``;
        }
        return html`<ak-tabs>
            <section
                slot="page-overview"
                data-tab-title="${msg("Overview")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            ></section>
            <section
                slot="page-events"
                data-tab-title="${msg("User events")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-events-user targetUser=${this._role.name}> </ak-events-user>
                    </div>
                </div>
            </section>
        </ak-tabs>`;
    }
}
