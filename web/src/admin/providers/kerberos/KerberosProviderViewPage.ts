import "@goauthentik/admin/providers/RelatedApplicationButton";
import "@goauthentik/admin/providers/kerberos/KerberosProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { convertToSlug } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/Markdown";
import { Replacer } from "@goauthentik/elements/Markdown";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/events/ObjectChangelog";
import { getURLParam } from "@goauthentik/elements/router/RouteMatch";

import { msg } from "@lit/localize";
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

import { ProvidersApi, KerberosApi, KerberosRealm, KerberosProvider } from "@goauthentik/api";

@customElement("ak-provider-kerberos-view")
export class KerberosProviderViewPage extends AKElement {
    @property()
    set args(value: { [key: string]: number }) {
        this.providerID = value.id;
    }

    @property({ type: Number })
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersKerberosRetrieve({
                id: value,
            })
            .then((prov) => (this.provider = prov));
    }

    @property({ attribute: false })
    provider?: KerberosProvider;

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
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` <ak-tabs>
            <section slot="page-overview" data-tab-title="${msg("Overview")}">
                ${this.renderTabOverview()}
            </section>
            <section slot="page-credentials" data-tab-title="${msg("Credentials")}">
                ${this.renderTabCredentials()}
            </section>
            <section
                slot="page-changelog"
                data-tab-title="${msg("Changelog")}"
                class="pf-c-page__main-section pf-m-no-padding-mobile"
            >
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-object-changelog
                            targetModelPk=${this.provider?.pk || ""}
                            targetModelName=${this.provider?.metaModelName || ""}
                        >
                        </ak-object-changelog>
                    </div>
                </div>
            </section>
        </ak-tabs>`;
    }

    renderTabOverview(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`${this.provider?.assignedApplicationName
                ? html``
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg("Warning: Provider is not used by an Application.")}
                  </div>`}
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
                                        ${this.provider.name}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("Service Principal Name")}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.provider.fullSpn}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Assigned to application")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <ak-provider-related-application
                                            .provider=${this.provider}
                                        ></ak-provider-related-application>
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-forms-modal>
                            <span slot="submit"> ${msg("Update")} </span>
                            <span slot="header"> ${msg("Update Kerberos Provider")} </span>
                            <ak-provider-kerberos-form
                                slot="form"
                                .instancePk=${this.provider.pk || 0}
                            >
                            </ak-provider-kerberos-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${msg("Edit")}
                            </button>
                        </ak-forms-modal>
                    </div>
                </div>
            </div>`;
    }

    renderTabCredentials(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`
            <section
                slot="page-credentials"
                data-tab-title="${msg("Credentials")}"
            >
                <div
                    class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
                >
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                        <div class="pf-c-card__title">${msg("Keytab")}</div>
                        <div class="pf-c-card__body">
                            <a
                                class="pf-c-button pf-m-primary"
                                target="_blank"
                                href=${this.provider.urlDownloadKeytab}
                            >
                                ${msg("Download Keytab")}
                            </a>
                        </div>
                    </div>
                </div>
            </section>`;
    }
}
