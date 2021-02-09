import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/CodeMirror";
import "../../elements/Tabs";
import { Page } from "../../elements/Page";
import { LDAPSource } from "../../api/sources/LDAP";
import { Source } from "../../api/Sources";
import { until } from "lit-html/directives/until";
import { DefaultClient } from "../../api/Client";

@customElement("ak-source-ldap-view")
export class LDAPSourceViewPage extends Page {
    pageTitle(): string {
        return gettext(`LDAP Source ${this.source?.name || ""}`);
    }
    pageDescription(): string | undefined {
        return;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-middleware";
    }

    @property({ type: String })
    set sourceSlug(slug: string) {
        LDAPSource.get(slug).then((s) => this.source = s);
    }

    @property({ attribute: false })
    source?: LDAPSource;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    constructor() {
        super();
        this.addEventListener("ak-refresh", () => {
            if (!this.source?.slug) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    renderContent(): TemplateResult {
        if (!this.source) {
            return html``;
        }
        return html`<ak-tabs>
                <section slot="page-1" data-tab-title="${gettext("Overview")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-u-display-flex pf-u-justify-content-center">
                        <div class="pf-u-w-75">
                            <div class="pf-c-card pf-c-card-aggregate">
                                <div class="pf-c-card__body">
                                    <dl class="pf-c-description-list pf-m-2-col-on-lg">
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Name")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.source.name}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Server URI")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">${this.source.server_uri}</div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Base DN")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    <ul>
                                                        <li>${this.source.base_dn}</li>
                                                    </ul>
                                                </div>
                                            </dd>
                                        </div>
                                    </dl>
                                </div>
                                <div class="pf-c-card__footer">
                                    <ak-modal-button href="${Source.adminUrl(`${this.source.pk}/update/`)}">
                                        <ak-spinner-button slot="trigger" class="pf-m-primary">
                                            ${gettext("Edit")}
                                        </ak-spinner-button>
                                        <div slot="modal"></div>
                                    </ak-modal-button>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
                <section slot="page-2" data-tab-title="${gettext("Sync")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-u-display-flex pf-u-justify-content-center">
                        <div class="pf-u-w-75">
                            <div class="pf-c-card pf-c-card-aggregate">
                                <div class="pf-c-card pf-c-card-aggregate">
                                    <div class="pf-c-card__title">
                                        <p>${gettext("Sync status")}</p>
                                    </div>
                                    <div class="pf-c-card__body">
                                        <p>
                                        ${until(LDAPSource.syncStatus(this.source.slug).then((ls) => {
                                            if (!ls.last_sync) {
                                                return gettext("Not synced in the last hour, check System tasks.");
                                            }
                                            const syncDate = new Date(ls.last_sync * 1000);
                                            return gettext(`Last sync: ${syncDate.toLocaleString()}`)
                                        }), "loading")}
                                        </p>
                                    </div>
                                    <div class="pf-c-card__footer">
                                        <ak-action-button method="PATCH" url="${DefaultClient.makeUrl(["sources", "ldap", this.source.slug])}">
                                            ${gettext("Retry Task")}
                                        </ak-action-button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }
}
