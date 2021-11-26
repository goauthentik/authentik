import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../../authentik.css";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ProvidersApi, ProxyMode, ProxyProvider } from "@goauthentik/api";

import MDNginxIngress from "../../../../../website/docs/providers/proxy/_nginx_ingress.md";
import MDNginxPM from "../../../../../website/docs/providers/proxy/_nginx_proxy_manager.md";
import MDNginxStandalone from "../../../../../website/docs/providers/proxy/_nginx_standalone.md";
import MDTraefikCompose from "../../../../../website/docs/providers/proxy/_traefik_compose.md";
import MDTraefikIngres from "../../../../../website/docs/providers/proxy/_traefik_ingress.md";
import MDTraefikStandalone from "../../../../../website/docs/providers/proxy/_traefik_standalone.md";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { EVENT_REFRESH } from "../../../constants";
import "../../../elements/CodeMirror";
import "../../../elements/Tabs";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/events/ObjectChangelog";
import "../RelatedApplicationButton";
import "./ProxyProviderForm";

export function ModeToLabel(action?: ProxyMode): string {
    if (!action) return "";
    switch (action) {
        case ProxyMode.Proxy:
            return t`Proxy`;
        case ProxyMode.ForwardSingle:
            return t`Forward auth (single application)`;
        case ProxyMode.ForwardDomain:
            return t`Forward auth (domain-level)`;
    }
}

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
            PFContent,
            PFForm,
            PFFormControl,
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

    renderConfigTemplate(tmpl: string): TemplateResult {
        // See website/docs/providers/proxy/forward_auth.mdx
        const final = tmpl
            .replaceAll("authentik.company", window.location.hostname)
            .replaceAll("outpost.company", window.location.hostname)
            .replaceAll("app.company", this.provider?.externalHost || "");
        return html`${unsafeHTML(final)}`;
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`${this.provider?.assignedApplicationName
                ? html``
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${t`Warning: Provider is not used by an Application.`}
                  </div>`}
            ${this.provider?.outpostSet.length < 1
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${t`Warning: Provider is not used by any Outpost.`}
                  </div>`
                : html``}
            <div class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-3-col-on-lg">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${t`Name`}</span>
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
                                            ? html`<span class="pf-c-button__icon pf-m-start">
                                                      <i
                                                          class="fas fa-check-circle"
                                                          aria-hidden="true"
                                                      ></i
                                                      >&nbsp; </span
                                                  >${t`Yes`}`
                                            : html`<span class="pf-c-button__icon pf-m-start">
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
                                    <span class="pf-c-description-list__text">${t`Mode`}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${ModeToLabel(this.provider.mode || ProxyMode.Proxy)}
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
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">${t`Protocol Settings`}</div>
                    <div class="pf-c-card__body">
                        <form class="pf-c-form">
                            <div class="pf-c-form__group">
                                <label class="pf-c-form__label">
                                    <span class="pf-c-form__label-text"
                                        >${t`Allowed Redirect URIs`}</span
                                    >
                                </label>
                                <input
                                    class="pf-c-form-control"
                                    readonly
                                    type="text"
                                    value=${this.provider.redirectUris}
                                />
                            </div>
                        </form>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">${t`Setup`}</div>
                    <div class="pf-c-card__body">
                        <ak-tabs pageIdentifier="proxy-setup">
                            <section
                                slot="page-nginx-ingress"
                                data-tab-title="${t`Nginx (Ingress)`}"
                                class="pf-c-page__main-section pf-m-light pf-m-no-padding-mobile"
                            >
                                ${this.renderConfigTemplate(MDNginxIngress.html)}
                            </section>
                            <section
                                slot="page-nginx-proxy-manager"
                                data-tab-title="${t`Nginx (Proxy Manager)`}"
                                class="pf-c-page__main-section pf-m-light pf-m-no-padding-mobile"
                            >
                                ${this.renderConfigTemplate(MDNginxPM.html)}
                            </section>
                            <section
                                slot="page-nginx-standalone"
                                data-tab-title="${t`Nginx (standalone)`}"
                                class="pf-c-page__main-section pf-m-light pf-m-no-padding-mobile"
                            >
                                ${this.renderConfigTemplate(MDNginxStandalone.html)}
                            </section>
                            <section
                                slot="page-traefik-ingress"
                                data-tab-title="${t`Traefik (Ingress)`}"
                                class="pf-c-page__main-section pf-m-light pf-m-no-padding-mobile"
                            >
                                ${this.renderConfigTemplate(MDTraefikIngres.html)}
                            </section>
                            <section
                                slot="page-traefik-compose"
                                data-tab-title="${t`Traefik (Compose)`}"
                                class="pf-c-page__main-section pf-m-light pf-m-no-padding-mobile"
                            >
                                ${this.renderConfigTemplate(MDTraefikCompose.html)}
                            </section>
                            <section
                                slot="page-traefik-standalone"
                                data-tab-title="${t`Traefik (Standalone)`}"
                                class="pf-c-page__main-section pf-m-light pf-m-no-padding-mobile"
                            >
                                ${this.renderConfigTemplate(MDTraefikStandalone.html)}
                            </section>
                        </ak-tabs>
                    </div>
                </div>
            </div>`;
    }
}
