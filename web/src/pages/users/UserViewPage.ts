import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import AKGlobal from "../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/CodeMirror";
import "../../elements/Tabs";
import "../../elements/events/ObjectChangelog";
import "../../elements/user/UserConsentList";
import "../../elements/oauth/UserCodeList";
import "../../elements/oauth/UserRefreshList";
import "../../elements/charts/UserChart";
import { Page } from "../../elements/Page";
import { CoreApi, User } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-user-view")
export class UserViewPage extends Page {
    pageTitle(): string {
        return gettext(`User ${this.user?.username || ""}`);
    }
    pageDescription(): string | undefined {
        return;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }

    @property({ type: Number })
    set userId(id: number) {
        new CoreApi(DEFAULT_CONFIG).coreUsersRead({
            id: id,
        }).then((user) => {
            this.user = user;
        });
    }

    @property({ attribute: false })
    user?: User;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFFlex, PFDisplay, PFGallery, PFContent, PFCard, PFDescriptionList, PFSizing, AKGlobal];
    }

    constructor() {
        super();
        this.addEventListener("ak-refresh", () => {
            if (!this.user?.pk) return;
            this.userId = this.user?.pk;
        });
    }

    renderContent(): TemplateResult {
        if (!this.user) {
            return html``;
        }
        return html`<ak-tabs>
                <section slot="page-1" data-tab-title="${gettext("Overview")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-l-gallery pf-m-gutter">
                        <div class="pf-c-card pf-c-card-aggregate pf-l-gallery__item pf-m-4-col" style="grid-column-end: span 3;grid-row-end: span 2;">
                            <div class="pf-c-card__body">
                                <ak-charts-user>
                                </ak-charts-user>
                            </div>
                        </div>
                    </div>
                </section>
                <section slot="page-2" data-tab-title="${gettext("Changelog")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.user.pk || ""}
                                targetModelApp="authentik_core"
                                targetModelName="user">
                            </ak-object-changelog>
                        </div>
                    </div>
                </section>
                <section slot="page-3" data-tab-title="${gettext("Explicit Consent")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-consent-list .userId="${(this.user.pk || 0).toString()}">
                            </ak-user-consent-list>
                        </div>
                    </div>
                </section>
                <section slot="page-4" data-tab-title="${gettext("OAuth Authorization Codes")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-oauth-code-list .userId="${(this.user.pk || 0).toString()}">
                            </ak-user-oauth-code-list>
                        </div>
                    </div>
                </section>
                <section slot="page-5" data-tab-title="${gettext("OAuth Refresh Codes")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-user-oauth-refresh-list .userId="${(this.user.pk || 0).toString()}">
                            </ak-user-oauth-refresh-list>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }
}
