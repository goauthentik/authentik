import "@goauthentik/admin/providers/kerberos/KerberosRealmForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/events/ObjectChangelog";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { KerberosApi, KerberosRealm } from "@goauthentik/api";

@customElement("ak-kerberos-realm-view")
export class KerberosRealmViewPage extends AKElement {
    @property()
    set realmID(value: number) {
        new KerberosApi(DEFAULT_CONFIG)
            .kerberosRealmsRetrieve({
                id: value,
            })
            .then((realm) => {
                this.realm = realm;
            });
    }

    @property({ attribute: false })
    realm!: KerberosRealm;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFPage,
            PFGrid,
            PFContent,
            PFList,
            PFForm,
            PFFormControl,
            PFCard,
            PFDescriptionList,
            PFBanner,
        ];
    }

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.realm?.pk) return;
            this.realmID = this.realm?.pk;
        });
    }

    render(): TemplateResult {
        if (!this.realm) {
            return html`<ak-page-header icon="pf-icon pf-icon-catalog" header=${msg("Loading")}>
            </ak-page-header> `;
        }
        return html`<ak-page-header
                icon="pf-icon pf-icon-catalog"
                header=${msg(str`Realm ${this.realm.name}`)}
            >
            </ak-page-header>
            <ak-tabs>
                <section slot="page-overview" data-tab-title="${msg("Overview")}">
                    ${this.renderTabOverview()}
                </section>
                <section
                    slot="page-changelog"
                    data-tab-title="${msg("Changelog")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.realm?.pk || ""}
                                targetModelName=${this.realm?.metaModelName || ""}
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }

    renderTabOverview(): TemplateResult {
        if (!this.realm) {
            return html``;
        }
        return html`
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-3-col-on-lg">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("Name")}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.realm.name}
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                </div>
            </div>
        `;
    }
}
