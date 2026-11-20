import "#admin/policies/BoundPoliciesList";
import "#admin/rbac/ak-rbac-object-permission-page";
import "#admin/sources/oauth/OAuthSourceDiagram";
import "#admin/events/ObjectChangelog";
import "#elements/CodeEditor";
import "#elements/Tabs";
import "#elements/buttons/SpinnerButton/index";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { aki } from "#common/api/client";
import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { modalInvoker } from "#elements/dialogs";
import { sourceBindingTypeNotices } from "#elements/sources/utils";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList, { DescriptionPair } from "#components/DescriptionList";

import { OAuthSourceForm } from "#admin/sources/oauth/OAuthSourceForm";

import { ModelEnum, OAuthSource, ProviderTypeEnum, SourcesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

export function ProviderToLabel(provider?: ProviderTypeEnum): string {
    switch (provider) {
        case undefined:
            return "";
        case ProviderTypeEnum.Openidconnect:
            return msg("Generic OpenID Connect");
        case ProviderTypeEnum.Apple:
            return "Apple";
        case ProviderTypeEnum.Discord:
            return "Discord";
        case ProviderTypeEnum.Entraid:
            return "Entra ID";
        case ProviderTypeEnum.Facebook:
            return "Facebook";
        case ProviderTypeEnum.Github:
            return "GitHub";
        case ProviderTypeEnum.Gitlab:
            return "GitLab";
        case ProviderTypeEnum.Google:
            return "Google";
        case ProviderTypeEnum.Idjagissuer:
            return msg("Identity Assertion Issuer", {
                id: "sources.oauth.id-jag-issuer.provider-type.label",
            });
        case ProviderTypeEnum.Mailcow:
            return "Mailcow";
        case ProviderTypeEnum.Okta:
            return "Okta";
        case ProviderTypeEnum.Patreon:
            return "Patreon";
        case ProviderTypeEnum.Reddit:
            return "Reddit";
        case ProviderTypeEnum.Slack:
            return "Slack";
        case ProviderTypeEnum.Twitch:
            return "Twitch";
        case ProviderTypeEnum.Twitter:
            return "Twitter";
        case ProviderTypeEnum.Wechat:
            return "WeChat";
        case ProviderTypeEnum.UnknownDefaultOpenApi:
            return msg("Unknown provider type");
    }
}

@customElement("ak-source-oauth-view")
export class OAuthSourceViewPage extends AKElement {
    @property({ type: String })
    set sourceSlug(value: string) {
        aki(SourcesApi)
            .sourcesOauthRetrieve({
                slug: value,
            })
            .then((source) => {
                this.source = source;
            });
    }

    @property({ attribute: false })
    source?: OAuthSource;

    static styles: CSSResult[] = [PFPage, PFButton, PFGrid, PFContent, PFCard, PFDescriptionList];

    constructor() {
        super();

        this.addEventListener(EVENT_REFRESH, () => {
            if (!this.source?.pk) return;
            this.sourceSlug = this.source?.slug;
        });
    }

    /**
     * Sign-in details, which an issuer that only signs identity assertions doesn't have:
     * it's identified by its issuer instead.
     */
    protected renderLoginDetails(): DescriptionPair[] {
        if (!this.source) return [];

        if (this.source.type?.assertionOnly) {
            return [
                [
                    msg("Issuer", { id: "sources.oauth.id-jag-issuer.issuer.label" }),
                    html`${this.source.idJagIssuer}`,
                ],
                [
                    msg("Trusted email domains", {
                        id: "sources.oauth.id-jag-issuer.email-domains.label",
                    }),
                    html`${(this.source.idJagEmailDomains ?? []).join(", ")}`,
                ],
            ];
        }

        return [
            [msg("Callback URL"), html`${this.source.callbackUrl}`],
            [msg("Access Key"), html`${this.source.consumerKey}`],
            [
                msg("Authorization URL"),
                html`${this.source.type?.authorizationUrl || this.source.authorizationUrl}`,
            ],
            [
                msg("Token URL"),
                html`${this.source.type?.accessTokenUrl || this.source.accessTokenUrl}`,
            ],
        ];
    }

    protected renderDiagram(): SlottedTemplateResult {
        if (!this.source || this.source.type?.assertionOnly) return nothing;

        return html`<div class="pf-c-card pf-l-grid__item pf-m-8-col">
            <div class="pf-c-card__title">${msg("Diagram")}</div>
            <div class="pf-c-card__body">
                <ak-source-oauth-diagram .source=${this.source}></ak-source-oauth-diagram>
            </div>
        </div>`;
    }

    render(): SlottedTemplateResult {
        if (!this.source) {
            return nothing;
        }

        return html`<main>
            <ak-tabs routed>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-overview"
                    id="page-overview"
                    aria-label="${msg("Overview")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-4-col">
                            <div class="pf-c-card__title">${msg("Details")}</div>
                            <div class="pf-c-card__body">
                                ${renderDescriptionList([
                                    [msg("Name"), html`${this.source.name}`],
                                    [
                                        msg("Provider Type"),
                                        html`${ProviderToLabel(this.source.providerType)}`,
                                    ],
                                    ...this.renderLoginDetails(),
                                    [
                                        msg("Related actions"),
                                        html`<button
                                            class="pf-c-button pf-m-primary pf-m-block"
                                            ${modalInvoker(OAuthSourceForm, {
                                                instancePk: this.source.slug,
                                            })}
                                        >
                                            ${msg("Edit")}
                                        </button>`,
                                    ],
                                ])}
                            </div>
                        </div>
                        ${this.renderDiagram()}
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-changelog"
                    id="page-changelog"
                    aria-label="${msg("Changelog")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <ak-object-changelog
                                targetModelPk=${this.source.pk || ""}
                                targetModelName=${ModelEnum.AuthentikSourcesOauthOauthsource}
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-policy-binding"
                    id="page-policy-binding"
                    aria-label="${msg("Policy Bindings")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                            <div class="pf-c-card__title">
                                ${msg(
                                    `These bindings control which users can access this source.
            You can only use policies here as access is checked before the user is authenticated.`,
                                )}
                            </div>
                            <ak-bound-policies-list
                                .target=${this.source.pk}
                                .typeNotices=${sourceBindingTypeNotices()}
                                .policyEngineMode=${this.source.policyEngineMode}
                            >
                            </ak-bound-policies-list>
                        </div>
                    </div>
                </div>
                <ak-rbac-object-permission-page
                    role="tabpanel"
                    tabindex="0"
                    slot="page-permissions"
                    id="page-permissions"
                    aria-label="${msg("Permissions")}"
                    model=${ModelEnum.AuthentikSourcesOauthOauthsource}
                    objectPk=${this.source.pk}
                ></ak-rbac-object-permission-page>
            </ak-tabs>
        </main>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-oauth-view": OAuthSourceViewPage;
    }
}
