import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../../authentik.css";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ProvidersApi, ProxyProvider } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import { EVENT_REFRESH } from "../../../constants";
import "../../../elements/CodeMirror";
import "../../../elements/Tabs";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/events/ObjectChangelog";
import { convertToTitle } from "../../../utils";
import "../RelatedApplicationButton";
import "./ProxyProviderForm";

@customElement("ak-provider-proxy-view")
export class ProxyProviderViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: number }) {
        this.providerID = value.id;
    }

    @property({ type: Number })
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersProxyRetrieve({
                id: value,
            })
            .then((prov) => (this.provider = prov));
    }

    @property({ attribute: false })
    provider?: ProxyProvider;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFPage,
            PFGrid,
            PFGallery,
            PFContent,
            PFCard,
            PFDescriptionList,
            PFBanner,
            AKGlobal,
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
        return html` ${this.provider?.assignedApplicationName
                ? html``
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${t`Warning: Provider is not used by an Application.`}
                  </div>`}
            ${this.provider?.outpostSet.length < 1
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${t`Warning: Provider is not used by any Outpost.`}
                  </div>`
                : html``}
            <ak-tabs>
                <section
                    slot="page-overview"
                    data-tab-title="${t`Overview`}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-l-grid__item pf-m-6-col">
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">
                                    <dl class="pf-c-description-list pf-m-3-col-on-lg">
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Name`}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${this.provider.name}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Assigned to application`}</span
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
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Internal Host`}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${this.provider.internalHost}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`External Host`}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${this.provider.externalHost}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Basic-Auth`}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${this.provider.basicAuthEnabled
                                                        ? html`<span
                                                                  class="pf-c-button__icon pf-m-start"
                                                              >
                                                                  <i
                                                                      class="fas fa-check-circle"
                                                                      aria-hidden="true"
                                                                  ></i
                                                                  >&nbsp; </span
                                                              >${t`Yes`}`
                                                        : html`<span
                                                                  class="pf-c-button__icon pf-m-start"
                                                              >
                                                                  <i
                                                                      class="fas fa-times-circle"
                                                                      aria-hidden="true"
                                                                  ></i
                                                                  >&nbsp; </span
                                                              >${t`No`}`}
                                                </div>
                                            </dd>
                                        </div>
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Mode`}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${convertToTitle(this.provider.mode || "")}
                                                </div>
                                            </dd>
                                        </div>
                                    </dl>
                                </div>
                                <div class="pf-c-card__footer">
                                    <ak-forms-modal>
                                        <span slot="submit"> ${t`Update`} </span>
                                        <span slot="header"> ${t`Update Proxy Provider`} </span>
                                        <ak-provider-proxy-form
                                            slot="form"
                                            .instancePk=${this.provider.pk || 0}
                                        >
                                        </ak-provider-proxy-form>
                                        <button slot="trigger" class="pf-c-button pf-m-primary">
                                            ${t`Edit`}
                                        </button>
                                    </ak-forms-modal>
                                </div>
                            </div>
                        </div>
                        <div class="pf-l-grid__item pf-m-6-col">
                            <div class="pf-c-card">
                                <div class="pf-c-card__title">${t`Protocol Settings`}</div>
                                <div class="pf-c-card__body">
                                    <dl class="pf-c-description-list pf-m-3-col-on-lg">
                                        <div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text"
                                                    >${t`Allowed Redirect URIs`}</span
                                                >
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    ${this.provider.redirectUris}
                                                </div>
                                            </dd>
                                        </div>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-changelog"
                    data-tab-title="${t`Changelog`}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.provider.pk || ""}
                                targetModelApp="authentik_providers_proxy"
                                targetModelName="proxyprovider"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }
}
