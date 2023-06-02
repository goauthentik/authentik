import "@goauthentik/admin/providers/RelatedApplicationButton";
import "@goauthentik/admin/providers/proxy/ProxyProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { convertToSlug } from "@goauthentik/common/utils";
import MDCaddyStandalone from "@goauthentik/docs/providers/proxy/_caddy_standalone.md";
import MDNginxIngress from "@goauthentik/docs/providers/proxy/_nginx_ingress.md";
import MDNginxPM from "@goauthentik/docs/providers/proxy/_nginx_proxy_manager.md";
import MDNginxStandalone from "@goauthentik/docs/providers/proxy/_nginx_standalone.md";
import MDTraefikCompose from "@goauthentik/docs/providers/proxy/_traefik_compose.md";
import MDTraefikIngress from "@goauthentik/docs/providers/proxy/_traefik_ingress.md";
import MDTraefikStandalone from "@goauthentik/docs/providers/proxy/_traefik_standalone.md";
import MDHeaderAuthentication from "@goauthentik/docs/providers/proxy/header_authentication.md";
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

import { ProvidersApi, ProxyMode, ProxyProvider } from "@goauthentik/api";

export function ModeToLabel(action?: ProxyMode): string {
    if (!action) return "";
    switch (action) {
        case ProxyMode.Proxy:
            return msg("Proxy");
        case ProxyMode.ForwardSingle:
            return msg("Forward auth (single application)");
        case ProxyMode.ForwardDomain:
            return msg("Forward auth (domain-level)");
        case ProxyMode.UnknownDefaultOpenApi:
            return msg("Unknown proxy mode");
    }
}

export function isForward(mode: ProxyMode): boolean {
    switch (mode) {
        case ProxyMode.Proxy:
            return false;
        case ProxyMode.ForwardSingle:
        case ProxyMode.ForwardDomain:
            return true;
        case ProxyMode.UnknownDefaultOpenApi:
            return false;
    }
}

@customElement("ak-provider-proxy-view")
export class ProxyProviderViewPage extends AKElement {
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

    renderConfig(): TemplateResult {
        const serves = [
            {
                label: msg("Nginx (Ingress)"),
                md: MDNginxIngress,
            },
            {
                label: msg("Nginx (Proxy Manager)"),
                md: MDNginxPM,
            },
            {
                label: msg("Nginx (standalone)"),
                md: MDNginxStandalone,
            },
            {
                label: msg("Traefik (Ingress)"),
                md: MDTraefikIngress,
            },
            {
                label: msg("Traefik (Compose)"),
                md: MDTraefikCompose,
            },
            {
                label: msg("Traefik (Standalone)"),
                md: MDTraefikStandalone,
            },
            {
                label: msg("Caddy (Standalone)"),
                md: MDCaddyStandalone,
            },
        ];
        const replacers: Replacer[] = [
            (input: string): string => {
                // The generated config is pretty unreliable currently so
                // put it behind a flag
                if (!getURLParam("generatedConfig", false)) {
                    return input;
                }
                if (!this.provider) {
                    return input;
                }
                const extHost = new URL(this.provider.externalHost);
                // See website/docs/providers/proxy/forward_auth.mdx
                if (this.provider?.mode === ProxyMode.ForwardSingle) {
                    return input
                        .replaceAll("authentik.company", window.location.hostname)
                        .replaceAll("outpost.company:9000", window.location.hostname)
                        .replaceAll("https://app.company", extHost.toString())
                        .replaceAll("app.company", extHost.hostname);
                } else if (this.provider?.mode == ProxyMode.ForwardDomain) {
                    return input
                        .replaceAll("authentik.company", window.location.hostname)
                        .replaceAll("outpost.company:9000", extHost.toString())
                        .replaceAll("https://app.company", extHost.toString())
                        .replaceAll("app.company", extHost.hostname);
                }
                return input;
            },
        ];
        return html`<ak-tabs pageIdentifier="proxy-setup">
            ${serves.map((server) => {
                return html`<section
                    slot="page-${convertToSlug(server.label)}"
                    data-tab-title="${server.label}"
                    class="pf-c-page__main-section pf-m-light pf-m-no-padding-mobile"
                >
                    <ak-markdown .replacers=${replacers} .md=${server.md}></ak-markdown>
                </section>`;
            })}</ak-tabs
        >`;
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html` <ak-tabs>
            <section slot="page-overview" data-tab-title="${msg("Overview")}">
                ${this.renderTabOverview()}
            </section>
            <section slot="page-authentication" data-tab-title="${msg("Authentication")}">
                ${this.renderTabAuthentication()}
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

    renderTabAuthentication(): TemplateResult {
        if (!this.provider) {
            return html``;
        }
        return html`<div
            class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter"
        >
            <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                <div class="pf-c-card__body">
                    <dl class="pf-c-description-list pf-m-3-col-on-lg">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${msg("Client ID")}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    <pre>${this.provider.clientId}</pre>
                                </div>
                            </dd>
                        </div>
                    </dl>
                </div>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                <div class="pf-c-card__body">
                    <ak-markdown .md=${MDHeaderAuthentication}></ak-markdown>
                </div>
            </div>
        </div>`;
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
            ${this.provider?.outpostSet.length < 1
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg("Warning: Provider is not used by any Outpost.")}
                  </div>`
                : html``}
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
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Internal Host")}</span
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
                                        >${msg("External Host")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <a target="_blank" href="${this.provider.externalHost}"
                                            >${this.provider.externalHost}</a
                                        >
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Basic-Auth")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <ak-label
                                            color=${this.provider.basicAuthEnabled
                                                ? PFColor.Green
                                                : PFColor.Grey}
                                        >
                                            ${this.provider.basicAuthEnabled
                                                ? msg("Yes")
                                                : msg("No")}
                                        </ak-label>
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("Mode")}</span>
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
                            <span slot="submit"> ${msg("Update")} </span>
                            <span slot="header"> ${msg("Update Proxy Provider")} </span>
                            <ak-provider-proxy-form
                                slot="form"
                                .instancePk=${this.provider.pk || 0}
                            >
                            </ak-provider-proxy-form>
                            <button slot="trigger" class="pf-c-button pf-m-primary">
                                ${msg("Edit")}
                            </button>
                        </ak-forms-modal>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">${msg("Protocol Settings")}</div>
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-3-col-on-lg">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Allowed Redirect URIs")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <ul class="pf-c-list">
                                            ${this.provider.redirectUris.split("\n").map((url) => {
                                                return html`<li><pre>${url}</pre></li>`;
                                            })}
                                        </ul>
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">${msg("Setup")}</div>
                    <div class="pf-c-card__body">
                        ${isForward(this.provider?.mode || ProxyMode.Proxy)
                            ? html` ${this.renderConfig()} `
                            : html` <p>${msg("No additional setup is required.")}</p> `}
                    </div>
                </div>
            </div>`;
    }
}
