import "@goauthentik/admin/sources/ldap/LDAPSourceViewPage";
import "@goauthentik/admin/sources/oauth/OAuthSourceViewPage";
import "@goauthentik/admin/sources/plex/PlexSourceViewPage";
import "@goauthentik/admin/sources/saml/SAMLSourceViewPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/buttons/SpinnerButton";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Source, SourcesApi } from "@goauthentik/api";

@customElement("ak-source-view")
export class SourceViewPage extends AKElement {
    @property({ type: String })
    set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesAllRetrieve({
                slug: slug,
            })
            .then((source) => {
                this.source = source;
            });
    }

    @property({ attribute: false })
    source?: Source;

    renderSource(): TemplateResult {
        if (!this.source) {
            return html`<ak-empty-state ?loading=${true} ?fullHeight=${true}></ak-empty-state>`;
        }
        switch (this.source?.component) {
            case "ak-source-ldap-form":
                return html`<ak-source-ldap-view
                    sourceSlug=${this.source.slug}
                ></ak-source-ldap-view>`;
            case "ak-source-oauth-form":
                return html`<ak-source-oauth-view
                    sourceSlug=${this.source.slug}
                ></ak-source-oauth-view>`;
            case "ak-source-saml-form":
                return html`<ak-source-saml-view
                    sourceSlug=${this.source.slug}
                ></ak-source-saml-view>`;
            case "ak-source-plex-form":
                return html`<ak-source-plex-view
                    sourceSlug=${this.source.slug}
                ></ak-source-plex-view>`;
            default:
                return html`<p>Invalid source type ${this.source.component}</p>`;
        }
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon="pf-icon pf-icon-middleware"
                header=${ifDefined(this.source?.name)}
                description=${ifDefined(this.source?.verboseName)}
            >
            </ak-page-header>
            ${this.renderSource()}`;
    }
}
