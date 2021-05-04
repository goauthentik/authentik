import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Source, SourcesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

import "../../elements/buttons/SpinnerButton";
import "../../elements/EmptyState";
import "../../elements/PageHeader";

import "./ldap/LDAPSourceViewPage";
import "./oauth/OAuthSourceViewPage";
import "./saml/SAMLSourceViewPage";
import "./plex/PlexSourceViewPage";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-source-view")
export class SourceViewPage extends LitElement {

    @property({ type: String })
    set sourceSlug(slug: string) {
        new SourcesApi(DEFAULT_CONFIG).sourcesAllRead({
            slug: slug
        }).then((source) => {
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
                return html`<ak-source-ldap-view sourceSlug=${this.source.slug}></ak-source-ldap-view>`;
            case "ak-source-oauth-form":
                return html`<ak-source-oauth-view sourceSlug=${this.source.slug}></ak-source-oauth-view>`;
            case "ak-source-saml-form":
                return html`<ak-source-saml-view sourceSlug=${this.source.slug}></ak-source-saml-view>`;
            case "ak-source-plex-form":
                return html`<ak-source-plex-view sourceSlug=${this.source.slug}></ak-source-plex-view>`;
            default:
                return html`<p>Invalid source type ${this.source.component}</p>`;
        }
    }

    render(): TemplateResult {
        return html`<ak-page-header
            icon="pf-icon pf-icon-middleware"
            header=${ifDefined(this.source?.name)}
            description=${ifDefined(this.source?.verboseName)}>
        </ak-page-header>
        ${this.renderSource()}`;
    }
}
