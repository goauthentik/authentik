import "#admin/providers/RelatedApplicationButton";
import "#admin/providers/proxy/ProxyProviderForm";
import "#admin/rbac/ObjectPermissionsPage";
import "#components/ak-status-label";
import "#components/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/Tabs";
import "#elements/ak-mdx/index";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";

import type { Replacer } from "#elements/ak-mdx/index";
import { AKElement } from "#elements/Base";
import { getURLParam } from "#elements/router/RouteMatch";
import { formatSlug } from "#elements/router/utils";
import { SlottedTemplateResult } from "#elements/types";

import {
    ProvidersApi,
    ProxyMode,
    ProxyProvider,
    RbacPermissionsAssignedByRolesListModelEnum,
} from "@goauthentik/api";

import MDCaddyStandalone from "~docs/add-secure-apps/providers/proxy/_caddy_standalone.md";
import MDNginxIngress from "~docs/add-secure-apps/providers/proxy/_nginx_ingress.md";
import MDNginxPM from "~docs/add-secure-apps/providers/proxy/_nginx_proxy_manager.md";
import MDNginxStandalone from "~docs/add-secure-apps/providers/proxy/_nginx_standalone.md";
import MDTraefikCompose from "~docs/add-secure-apps/providers/proxy/_traefik_compose.md";
import MDTraefikIngress from "~docs/add-secure-apps/providers/proxy/_traefik_ingress.md";
import MDTraefikStandalone from "~docs/add-secure-apps/providers/proxy/_traefik_standalone.md";
import MDHeaderAuthentication from "~docs/add-secure-apps/providers/proxy/header_authentication.mdx";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

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
    @property({ type: Number })
    providerID?: number;

    @state()
    provider?: ProxyProvider;

    static styles: CSSResult[] = [
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
        css`
            :host(:not([theme="dark"])) .ak-markdown-section {
                background-color: var(--pf-c-card--BackgroundColor);
            }
        `,
    ];

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.provider?.pk) return;
            this.providerID = this.provider?.pk;
        });
    }

    fetchProvider(id: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersProxyRetrieve({ id })
            .then((prov) => (this.provider = prov));
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("providerID") && this.providerID) {
            this.fetchProvider(this.providerID);
        }
    }

    renderConfig(): TemplateResult {
        const servers = [
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
                // See website/docs/add-secure-apps/providers/proxy/forward_auth.mdx
                if (this.provider?.mode === ProxyMode.ForwardSingle) {
                    return input
                        .replaceAll("authentik.company", window.location.hostname)
                        .replaceAll("outpost.company:9000", window.location.hostname)
                        .replaceAll("https://app.company", extHost.toString())
                        .replaceAll("app.company", extHost.hostname);
                } else if (this.provider?.mode === ProxyMode.ForwardDomain) {
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
            ${servers.map((server) => {
                return html`<div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-${formatSlug(server.label)}"
                    id="page-${formatSlug(server.label)}"
                    aria-label="${server.label}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile ak-markdown-section"
                >
                    <ak-mdx .url=${server.md} .replacers=${replacers}></ak-mdx>
                </div>`;
            })}</ak-tabs
        >`;
    }

    render(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }
        return html`<main part="main">
            <ak-tabs part="tabs">
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                >
                    ${this.renderTabOverview()}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-authentication"
                    id="page-authentication"
                    aria-label="${msg("Authentication")}"
                >
                    ${this.renderTabAuthentication()}
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-changelog"
                    id="page-changelog"
                    aria-label="${msg("Changelog")}"
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
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikProvidersProxyProxyprovider}
                    objectPk=${this.provider.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }

    renderTabAuthentication(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
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
                    <ak-mdx .url=${MDHeaderAuthentication}></ak-mdx>
                </div>
            </div>
        </div>`;
    }

    renderTabOverview(): SlottedTemplateResult {
        if (!this.provider) {
            return nothing;
        }
        return html`${this.provider?.assignedApplicationName
                ? nothing
                : html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg("Warning: Provider is not used by an Application.")}
                  </div>`}
            ${this.provider?.outpostSet.length < 1
                ? html`<div slot="header" class="pf-c-banner pf-m-warning">
                      ${msg("Warning: Provider is not used by any Outpost.")}
                  </div>`
                : nothing}
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
                                        <ak-status-label
                                            type="info"
                                            ?good=${this.provider.basicAuthEnabled}
                                        ></ak-status-label>
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
                            <span slot="submit">${msg("Update")}</span>
                            <span slot="header">${msg("Update Proxy Provider")}</span>
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
                                            <ul>
                                                ${this.provider.redirectUris.map((ru) => {
                                                    return html`<li>
                                                        ${ru.matchingMode}: ${ru.url}
                                                    </li>`;
                                                })}
                                            </ul>
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-proxy-view": ProxyProviderViewPage;
    }
}
